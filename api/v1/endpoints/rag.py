# -*- coding: utf-8 -*-
"""
RAG API Endpoints
"""

import logging
import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query

from api.v1.schemas.rag import (
    StrategyUploadResponse,
    StrategyListResponse,
    StrategyInfo,
    RetrievalResponse,
    RetrievalResult,
    StrategyDeleteResponse,
)
from src.rag.retriever import get_retriever, StrategyRetriever

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/strategies/upload", response_model=StrategyUploadResponse)
async def upload_strategy(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    """
    上传策略文件并向量化
    
    支持的文件格式：PDF、DOC、DOCX、TXT、图片（PNG/JPG/JPEG/BMP/GIF）
    """
    retriever = get_retriever()

    allowed_extensions = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        strategy_id = retriever.add_strategy(
            file_path=tmp_path,
            strategy_name=name,
            description=description,
        )

        strategy = retriever.get_strategy(strategy_id)
        
        return StrategyUploadResponse(
            strategy_id=strategy_id,
            name=strategy.name if strategy else name or file.filename,
            chunk_count=strategy.chunk_count if strategy else 0,
            message="策略上传并向量化成功",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"策略上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"策略上传失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/strategies", response_model=StrategyListResponse)
def list_strategies():
    """获取所有已上传的策略列表"""
    retriever = get_retriever()
    strategies = retriever.list_strategies()
    
    return StrategyListResponse(
        strategies=[s.to_dict() for s in strategies],
        total=len(strategies),
    )


@router.get("/strategies/{strategy_id}", response_model=StrategyInfo)
def get_strategy(strategy_id: str):
    """获取指定策略详情"""
    retriever = get_retriever()
    strategy = retriever.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return strategy.to_dict()


@router.delete("/strategies/{strategy_id}", response_model=StrategyDeleteResponse)
def delete_strategy(strategy_id: str):
    """删除指定策略"""
    retriever = get_retriever()
    success = retriever.delete_strategy(strategy_id)
    
    return StrategyDeleteResponse(
        success=success,
        message="策略删除成功" if success else "策略删除失败"
    )


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_strategy(
    query: str = Query(..., description="检索query"),
    top_k: int = Query(5, ge=1, le=20, description="返回结果数量"),
    strategy_id: Optional[str] = Query(None, description="指定策略ID，不指定则全局检索"),
):
    """
    根据 query 检索相关策略片段
    """
    retriever = get_retriever()
    
    try:
        results = retriever.retrieve(query=query, top_k=top_k, strategy_id=strategy_id)
        
        return RetrievalResponse(
            query=query,
            results=[r.to_dict() for r in results],
            strategy_id=strategy_id,
        )
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")