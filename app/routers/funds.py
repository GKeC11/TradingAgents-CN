"""
Fund query API routes.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.response import ok
from app.routers.auth_db import get_current_user
from app.services.fund_data_service import get_fund_data_service

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/search", response_model=Dict[str, Any])
async def search_funds(
    query: str = Query("", description="Fund code, name, or pinyin"),
    limit: int = Query(20, ge=1, le=50, description="Max result count"),
    current_user: dict = Depends(get_current_user),
):
    try:
        service = get_fund_data_service()
        result = await service.search_funds(query=query, limit=limit)
        return ok(data=result, message="基金搜索成功")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"基金搜索失败: {exc}")


@router.get("/{fund_code}", response_model=Dict[str, Any])
async def get_fund_detail(
    fund_code: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        service = get_fund_data_service()
        result = await service.get_fund_detail(fund_code)
        if not result.get("basic_info") and not result.get("latest_nav"):
            warnings = result.get("data_warnings") or ["未找到基金数据"]
            return ok(data=result, message="; ".join(warnings))
        return ok(data=result, message="基金详情获取成功")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"基金详情获取失败: {exc}")


@router.get("/{fund_code}/nav", response_model=Dict[str, Any])
async def get_fund_nav(
    fund_code: str,
    period: str = Query("1y", description="1m|3m|6m|1y|3y|all"),
    current_user: dict = Depends(get_current_user),
):
    try:
        service = get_fund_data_service()
        result = await service.get_nav_history(fund_code, period=period)
        return ok(data=result, message="基金净值获取成功")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"基金净值获取失败: {exc}")


@router.get("/{fund_code}/holdings", response_model=Dict[str, Any])
async def get_fund_holdings(
    fund_code: str,
    year: Optional[str] = Query(None, description="Disclosure year, defaults to current year"),
    current_user: dict = Depends(get_current_user),
):
    try:
        service = get_fund_data_service()
        result = await service.get_holdings(fund_code, year=year)
        return ok(data=result, message="基金持仓获取成功")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"基金持仓获取失败: {exc}")


@router.post("/{fund_code}/refresh", response_model=Dict[str, Any])
async def refresh_fund(
    fund_code: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        service = get_fund_data_service()
        result = await service.refresh_fund(fund_code)
        return ok(data=result, message="基金缓存刷新成功")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"基金缓存刷新失败: {exc}")
