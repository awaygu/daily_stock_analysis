# -*- coding: utf-8 -*-
"""
向量存储 - FAISS 索引 + SQLite 元数据
"""

import json
import logging
import os
import sqlite3
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from src.rag.config import get_rag_config

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, index_path: Optional[str] = None, meta_path: Optional[str] = None):
        self.config = get_rag_config()
        self.index_path = index_path or str(self.config.get_vector_db_dir() / self.config.VECTOR_INDEX_FILE)
        self.meta_path = meta_path or str(self.config.get_vector_db_dir() / self.config.VECTOR_META_FILE)
        self.embedding_dim = self.config.EMBEDDING_DIM

        self._init_metadata_db()

    def _init_metadata_db(self) -> None:
        Path(self.meta_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.meta_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_chunks (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                source TEXT NOT NULL,
                page INTEGER,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
        conn.close()

    def _load_faiss_index(self):
        try:
            import faiss
            return faiss
        except ImportError:
            logger.warning("faiss 未安装，尝试安装 faiss-cpu")
            try:
                import subprocess
                subprocess.check_call(["pip", "install", "faiss-cpu"])
                import faiss
                return faiss
            except Exception as e:
                logger.error(f"faiss 安装失败: {e}")
                return None

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.meta_path)

    def add_chunks(
        self,
        strategy_id: str,
        strategy_name: str,
        file_path: str,
        file_type: str,
        chunks: List[Tuple[str, Optional[int], List[float]]],
    ) -> int:
        import faiss

        ids = []
        vectors = []

        for chunk_content, page, embedding in chunks:
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            vectors.append(embedding)

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO strategy_chunks (id, strategy_id, strategy_name, source, page, content, chunk_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, strategy_id, strategy_name, file_path, page, chunk_content, len(ids) - 1),
            )
            conn.commit()
            conn.close()

        if not vectors:
            return 0

        vectors_array = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_array)

        if os.path.exists(self.index_path):
            index = faiss.read_index(self.index_path)
            index.add(vectors_array)
        else:
            index = faiss.IndexFlatIP(self.embedding_dim)
            index.add(vectors_array)

        faiss.write_index(index, self.index_path)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO strategies (id, name, file_path, file_type, chunk_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (strategy_id, strategy_name, file_path, file_type, len(chunks)),
        )
        conn.commit()
        conn.close()

        logger.info(f"已添加 {len(chunks)} 个 chunks 到策略 {strategy_name}")
        return len(chunks)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, str, float, Optional[int]]]:
        import faiss

        if not os.path.exists(self.index_path):
            return []

        query_np = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_np)

        index = faiss.read_index(self.index_path)
        distances, indices = index.search(query_np, min(top_k, index.ntotal))

        results = []
        conn = self._get_connection()
        cursor = conn.cursor()

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            cursor.execute(
                "SELECT content, source, page FROM strategy_chunks WHERE chunk_index = ?",
                (int(idx),),
            )
            row = cursor.fetchone()
            if row:
                content, source, page = row
                results.append((content, source, float(dist), page))

        conn.close()
        return results

    def delete_strategy(self, strategy_id: str) -> bool:
        import faiss

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT chunk_index FROM strategy_chunks WHERE strategy_id = ?", (strategy_id,))
        chunk_indices = [row[0] for row in cursor.fetchall()]

        cursor.execute("DELETE FROM strategy_chunks WHERE strategy_id = ?", (strategy_id,))
        cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
        conn.commit()
        conn.close()

        if os.path.exists(self.index_path) and chunk_indices:
            index = faiss.read_index(self.index_path)
            if index.ntotal > 0:
                mask = np.ones(index.ntotal, dtype=np.bool_)
                for idx in chunk_indices:
                    if 0 <= idx < len(mask):
                        mask[idx] = False
                if not mask.all():
                    index.remove_ids(faiss.IDSelectorBatch(np.where(mask)[0]))
                    faiss.write_index(index, self.index_path)

        logger.info(f"已删除策略 {strategy_id}")
        return True

    def list_strategies(self) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, file_type, chunk_count, created_at FROM strategies")
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "file_type": row[3],
                "chunk_count": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def get_strategy(self, strategy_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, file_path, file_type, chunk_count, created_at FROM strategies WHERE id = ?",
            (strategy_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "file_path": row[3],
            "file_type": row[4],
            "chunk_count": row[5],
            "created_at": row[6],
        }