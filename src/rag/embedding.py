# -*- coding: utf-8 -*-
"""
DASHSCOPE Embedding 服务
"""

import logging
import os
from typing import List, Optional

import httpx

from src.rag.config import get_rag_config

logger = logging.getLogger(__name__)


class DASHSCOPEEmbedding:
    def __init__(self, api_key: Optional[str] = None):
        self.config = get_rag_config()
        self.api_key = api_key or self.config.DASHSCOPE_API_KEY
        self.model = self.config.DASHSCOPE_EMBEDDING_MODEL
        self.url = self.config.DASHSCOPE_EMBEDDING_URL

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 未设置，返回零向量")
            return [[0.0] * self.config.EMBEDDING_DIM for _ in texts]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": {"texts": texts},
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

            embeddings = []
            if "data" in result:
                for item in result["data"]:
                    if "embedding" in item:
                        embeddings.append(item["embedding"])
                    else:
                        embeddings.append([0.0] * self.config.EMBEDDING_DIM)
                return embeddings
            return [[0.0] * self.config.EMBEDDING_DIM for _ in texts]
        except Exception as e:
            logger.error(f"DASHSCOPE embedding 请求失败: {e}")
            return [[0.0] * self.config.EMBEDDING_DIM for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        result = self.embed([query])
        return result[0] if result else [0.0] * self.config.EMBEDDING_DIM