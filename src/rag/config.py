# -*- coding: utf-8 -*-
"""
RAG 模块配置
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


class RAGConfig:
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v1"
    DASHSCOPE_EMBEDDING_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/text-embedding/v1"

    VECTOR_DB_PATH: Path = Path(os.getenv("VECTOR_DB_PATH", "./data/vector_db"))
    VECTOR_INDEX_FILE: str = "strategies.index"
    VECTOR_META_FILE: str = "strategies_meta.db"

    EMBEDDING_DIM: int = 1536

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    RETRIEVAL_TOP_K: int = 5

    @classmethod
    def get_vector_db_dir(cls) -> Path:
        path = cls.VECTOR_DB_PATH
        path.mkdir(parents=True, exist_ok=True)
        return path


def get_rag_config() -> RAGConfig:
    return RAGConfig()