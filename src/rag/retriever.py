# -*- coding: utf-8 -*-
"""
策略检索器 - RAG 核心接口
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional

from src.rag.config import get_rag_config
from src.rag.document_parser import DocumentParser, parse_document
from src.rag.embedding import DASHSCOPEEmbedding
from src.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalResult:
    def __init__(self, content: str, source: str, score: float, page: Optional[int] = None):
        self.content = content
        self.source = source
        self.score = score
        self.page = page

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source": self.source,
            "score": self.score,
            "page": self.page,
        }


class StrategyInfo:
    def __init__(self, id: str, name: str, description: Optional[str], file_type: str, chunk_count: int, created_at: str):
        self.id = id
        self.name = name
        self.description = description
        self.file_type = file_type
        self.chunk_count = chunk_count
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "file_type": self.file_type,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
        }


class StrategyRetriever:
    def __init__(self):
        self.config = get_rag_config()
        self.parser = DocumentParser(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
        )
        self.embedding = DASHSCOPEEmbedding()
        self.vector_store = VectorStore()

    def add_strategy(self, file_path: str, strategy_name: Optional[str] = None, description: Optional[str] = None) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        path = Path(file_path)
        name = strategy_name or path.stem
        file_type = path.suffix.lower()
        strategy_id = str(uuid.uuid4())

        chunks = self.parser.parse_file(file_path)
        if not chunks:
            raise ValueError(f"无法从文件中解析出文本内容: {file_path}")

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding.embed(texts)

        chunk_data = [
            (chunk.content, chunk.page, emb)
            for chunk, emb in zip(chunks, embeddings)
        ]

        self.vector_store.add_chunks(
            strategy_id=strategy_id,
            strategy_name=name,
            file_path=str(path.absolute()),
            file_type=file_type,
            chunks=chunk_data,
        )

        logger.info(f"策略 {name} (ID: {strategy_id}) 已添加，共 {len(chunks)} 个 chunks")
        return strategy_id

    def retrieve(self, query: str, top_k: Optional[int] = None, strategy_id: Optional[str] = None) -> List[RetrievalResult]:
        if not query or not query.strip():
            return []

        query_embedding = self.embedding.embed_query(query)
        top_k = top_k or self.config.RETRIEVAL_TOP_K

        raw_results = self.vector_store.search(query_embedding, top_k)

        results = []
        for content, source, score, page in raw_results:
            result = RetrievalResult(content=content, source=source, score=score, page=page)
            results.append(result)

        return results

    def delete_strategy(self, strategy_id: str) -> bool:
        return self.vector_store.delete_strategy(strategy_id)

    def list_strategies(self) -> List[StrategyInfo]:
        strategy_dicts = self.vector_store.list_strategies()
        return [StrategyInfo(**s) for s in strategy_dicts]

    def get_strategy(self, strategy_id: str) -> Optional[StrategyInfo]:
        strategy_dict = self.vector_store.get_strategy(strategy_id)
        if strategy_dict:
            return StrategyInfo(**strategy_dict)
        return None


_retriever_instance: Optional[StrategyRetriever] = None


def get_retriever() -> StrategyRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = StrategyRetriever()
    return _retriever_instance