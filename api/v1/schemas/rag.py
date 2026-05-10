# -*- coding: utf-8 -*-
"""
RAG API Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class StrategyUploadResponse(BaseModel):
    strategy_id: str
    name: str
    chunk_count: int
    message: str


class StrategyInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    file_type: str
    chunk_count: int
    created_at: str


class StrategyListResponse(BaseModel):
    strategies: List[StrategyInfo]
    total: int


class RetrievalResult(BaseModel):
    content: str
    source: str
    score: float
    page: Optional[int] = None


class RetrievalResponse(BaseModel):
    query: str
    results: List[RetrievalResult]
    strategy_id: Optional[str] = None


class StrategyDeleteResponse(BaseModel):
    success: bool
    message: str


class StrategyUploadRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AnalyzeWithStrategyRequest(BaseModel):
    stocks: List[str] = Field(..., description="股票代码列表")
    strategy_id: str = Field(..., description="策略ID")
    language: Optional[str] = Field("zh", description="报告语言")