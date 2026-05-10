# -*- coding: utf-8 -*-
"""
RAG - Retrieval Augmented Generation 模块

职责：
1. 文档解析：支持 PDF、DOC、DOCX、TXT、图片等格式
2. 向量化：使用 DASHSCOPE text-embedding-v1 模型
3. 向量存储：FAISS 索引 + SQLite 元数据
4. 检索：根据查询检索相关策略片段
"""

from src.rag.retriever import StrategyRetriever

__all__ = ["StrategyRetriever"]