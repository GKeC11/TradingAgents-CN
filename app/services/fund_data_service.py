"""
Fund data service with cache-first access.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pymongo import UpdateOne

from app.core.database import get_mongo_db
from tradingagents.dataflows.providers.china.fund import ChinaFundProvider

logger = logging.getLogger(__name__)


class FundDataService:
    search_index_collection = "fund_search_index"
    basic_info_collection = "fund_basic_info"
    nav_history_collection = "fund_nav_history"
    performance_collection = "fund_performance"
    fee_info_collection = "fund_fee_info"
    holdings_collection = "fund_holdings"

    search_index_ttl_hours = 24
    basic_info_ttl_hours = 24 * 7
    nav_ttl_hours = 12
    performance_ttl_hours = 24
    fee_info_ttl_hours = 24 * 7
    holdings_ttl_hours = 24

    def __init__(self):
        self._provider: Optional[ChinaFundProvider] = None
        self._indexes_ready = False

    @property
    def provider(self) -> ChinaFundProvider:
        if self._provider is None:
            self._provider = ChinaFundProvider()
        return self._provider

    async def search_funds(self, query: str, limit: int = 20) -> Dict[str, Any]:
        await self.ensure_indexes()
        warnings: List[str] = []
        cache_status = await self._ensure_search_index()
        warnings.extend(cache_status.get("warnings", []))

        db = get_mongo_db()
        collection = db[self.search_index_collection]
        cleaned = str(query or "").strip()
        safe_limit = max(1, min(int(limit or 20), 50))

        if not cleaned:
            mongo_query: Dict[str, Any] = {}
        else:
            escaped = re.escape(cleaned)
            mongo_query = {
                "$or": [
                    {"fund_code": {"$regex": f"^{escaped}", "$options": "i"}},
                    {"fund_name": {"$regex": escaped, "$options": "i"}},
                    {"pinyin_abbr": {"$regex": f"^{escaped}", "$options": "i"}},
                    {"pinyin_full": {"$regex": escaped, "$options": "i"}},
                ]
            }

        cursor = collection.find(mongo_query, {"_id": 0}).sort("fund_code", 1).limit(safe_limit)
        items = await cursor.to_list(length=safe_limit)

        return {
            "items": [self._clean_doc(item) for item in items],
            "total": len(items),
            "query": cleaned,
            "cache_status": cache_status,
            "data_warnings": warnings,
        }

    async def get_fund_detail(self, fund_code: str) -> Dict[str, Any]:
        await self.ensure_indexes()
        code = self._normalize_code(fund_code)
        warnings: List[str] = []
        cache_status: Dict[str, Any] = {}

        for name, loader in [
            ("basic_info", self._ensure_basic_info),
            ("nav_history", self._ensure_nav_history),
            ("performance", self._ensure_performance),
            ("fee_info", self._ensure_fee_info),
            ("holdings", self._ensure_holdings),
        ]:
            status = await loader(code)
            cache_status[name] = {k: v for k, v in status.items() if k != "warnings"}
            warnings.extend(status.get("warnings", []))

        db = get_mongo_db()
        basic = await db[self.basic_info_collection].find_one({"fund_code": code}, {"_id": 0})
        latest_nav = await db[self.nav_history_collection].find_one(
            {"fund_code": code},
            {"_id": 0},
            sort=[("nav_date", -1)],
        )
        nav_docs = await db[self.nav_history_collection].find(
            {"fund_code": code},
            {"_id": 0},
        ).sort("nav_date", -1).limit(240).to_list(length=240)
        nav_docs = list(reversed(nav_docs))
        performance = await db[self.performance_collection].find(
            {"fund_code": code},
            {"_id": 0},
        ).to_list(length=100)
        fee_info = await db[self.fee_info_collection].find_one({"fund_code": code}, {"_id": 0})
        holdings = await db[self.holdings_collection].find_one(
            {"fund_code": code},
            {"_id": 0},
            sort=[("request_year", -1), ("updated_at", -1)],
        )

        if not basic and not latest_nav and not performance and not fee_info and not holdings:
            warnings.append("未找到该基金的可用数据")

        return {
            "basic_info": self._clean_doc(basic) if basic else None,
            "latest_nav": self._clean_doc(latest_nav) if latest_nav else None,
            "nav_history": [self._clean_doc(doc) for doc in nav_docs],
            "performance": [self._clean_doc(doc) for doc in performance],
            "fee_info": self._clean_doc(fee_info) if fee_info else None,
            "holdings": self._clean_doc(holdings) if holdings else None,
            "data_warnings": warnings,
            "cache_status": cache_status,
        }

    async def get_nav_history(self, fund_code: str, period: str = "1y") -> Dict[str, Any]:
        await self.ensure_indexes()
        code = self._normalize_code(fund_code)
        status = await self._ensure_nav_history(code)
        start_date = self._period_start_date(period)

        query: Dict[str, Any] = {"fund_code": code}
        if start_date:
            query["nav_date"] = {"$gte": start_date}

        db = get_mongo_db()
        docs = await db[self.nav_history_collection].find(query, {"_id": 0}).sort("nav_date", 1).to_list(length=5000)
        return {
            "fund_code": code,
            "period": period,
            "items": [self._clean_doc(doc) for doc in docs],
            "cache_status": {k: v for k, v in status.items() if k != "warnings"},
            "data_warnings": status.get("warnings", []),
        }

    async def refresh_fund(self, fund_code: str) -> Dict[str, Any]:
        await self.ensure_indexes()
        code = self._normalize_code(fund_code)
        await self._refresh_basic_info(code)
        await self._refresh_nav_history(code)
        await self._refresh_performance(code)
        await self._refresh_fee_info(code)
        await self._refresh_holdings(code)
        return await self.get_fund_detail(code)

    async def get_holdings(self, fund_code: str, year: Optional[str] = None) -> Dict[str, Any]:
        await self.ensure_indexes()
        code = self._normalize_code(fund_code)
        request_year = self._normalize_year(year)
        status = await self._ensure_holdings(code, request_year)

        db = get_mongo_db()
        doc = await db[self.holdings_collection].find_one(
            {"fund_code": code, "request_year": request_year},
            {"_id": 0},
        )
        if not doc:
            doc = await db[self.holdings_collection].find_one(
                {"fund_code": code},
                {"_id": 0},
                sort=[("request_year", -1), ("updated_at", -1)],
            )

        return {
            "fund_code": code,
            "request_year": request_year,
            "holdings": self._clean_doc(doc) if doc else None,
            "cache_status": {k: v for k, v in status.items() if k != "warnings"},
            "data_warnings": status.get("warnings", []),
        }

    async def refresh_search_index(self, force: bool = False) -> Dict[str, Any]:
        await self.ensure_indexes()
        if not force:
            status = await self._search_index_status()
            if status["exists"] and not status["stale"]:
                return status

        warnings: List[str] = []
        try:
            items = await asyncio.to_thread(self.provider.fetch_fund_list)
            now = datetime.utcnow()
            operations = []
            for item in items:
                item["updated_at"] = now
                operations.append(
                    UpdateOne(
                        {"fund_code": item["fund_code"]},
                        {"$set": item},
                        upsert=True,
                    )
                )

            if operations:
                db = get_mongo_db()
                await db[self.search_index_collection].bulk_write(operations, ordered=False)

            status = await self._search_index_status()
            status["refreshed"] = True
            status["warnings"] = warnings
            return status
        except Exception as exc:
            logger.warning("Refresh fund search index failed: %s", exc, exc_info=True)
            status = await self._search_index_status()
            status["warnings"] = [f"基金搜索索引刷新失败: {exc}"]
            status["refreshed"] = False
            return status

    async def ensure_indexes(self) -> None:
        if self._indexes_ready:
            return

        db = get_mongo_db()
        await db[self.search_index_collection].create_index([("fund_code", 1)], unique=True)
        await db[self.search_index_collection].create_index([("fund_name", 1)])
        await db[self.search_index_collection].create_index([("pinyin_abbr", 1)])
        await db[self.basic_info_collection].create_index([("fund_code", 1)], unique=True)
        await db[self.nav_history_collection].create_index([("fund_code", 1), ("nav_date", 1)], unique=True)
        await db[self.nav_history_collection].create_index([("fund_code", 1), ("updated_at", -1)])
        await db[self.performance_collection].create_index(
            [("fund_code", 1), ("performance_type", 1), ("period", 1)],
            unique=True,
        )
        await db[self.fee_info_collection].create_index([("fund_code", 1)], unique=True)
        await db[self.holdings_collection].create_index([("fund_code", 1), ("request_year", 1)], unique=True)
        await db[self.holdings_collection].create_index([("fund_code", 1), ("updated_at", -1)])
        self._indexes_ready = True

    async def _ensure_search_index(self) -> Dict[str, Any]:
        status = await self._search_index_status()
        if not status["exists"] or status["stale"]:
            return await self.refresh_search_index(force=True)
        status["warnings"] = []
        return status

    async def _search_index_status(self) -> Dict[str, Any]:
        db = get_mongo_db()
        latest = await db[self.search_index_collection].find_one({}, {"_id": 0, "updated_at": 1}, sort=[("updated_at", -1)])
        count = await db[self.search_index_collection].estimated_document_count()
        stale = True
        latest_at = latest.get("updated_at") if latest else None
        if latest_at:
            stale = self._is_stale(latest_at, self.search_index_ttl_hours)
        return {
            "exists": count > 0,
            "count": count,
            "stale": stale,
            "latest_updated_at": latest_at,
            "refreshed": False,
        }

    async def _ensure_basic_info(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        doc = await db[self.basic_info_collection].find_one({"fund_code": code}, {"_id": 0})
        if doc and not self._is_stale(doc.get("updated_at"), self.basic_info_ttl_hours):
            return {"exists": True, "stale": False, "warnings": []}
        return await self._refresh_basic_info(code)

    async def _ensure_nav_history(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        doc = await db[self.nav_history_collection].find_one({"fund_code": code}, {"_id": 0}, sort=[("updated_at", -1)])
        if doc and not self._is_stale(doc.get("updated_at"), self.nav_ttl_hours):
            return {"exists": True, "stale": False, "warnings": []}
        return await self._refresh_nav_history(code)

    async def _ensure_performance(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        doc = await db[self.performance_collection].find_one({"fund_code": code}, {"_id": 0}, sort=[("updated_at", -1)])
        if doc and not self._is_stale(doc.get("updated_at"), self.performance_ttl_hours):
            return {"exists": True, "stale": False, "warnings": []}
        return await self._refresh_performance(code)

    async def _ensure_fee_info(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        doc = await db[self.fee_info_collection].find_one({"fund_code": code}, {"_id": 0})
        if doc and not self._is_stale(doc.get("updated_at"), self.fee_info_ttl_hours):
            return {"exists": True, "stale": False, "warnings": []}
        return await self._refresh_fee_info(code)

    async def _ensure_holdings(self, code: str, year: Optional[str] = None) -> Dict[str, Any]:
        request_year = self._normalize_year(year)
        db = get_mongo_db()
        doc = await db[self.holdings_collection].find_one(
            {"fund_code": code, "request_year": request_year},
            {"_id": 0},
        )
        if doc and not self._is_stale(doc.get("updated_at"), self.holdings_ttl_hours):
            return {"exists": True, "stale": False, "warnings": []}
        return await self._refresh_holdings(code, request_year)

    async def _refresh_basic_info(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        warnings: List[str] = []
        try:
            data, provider_warnings = await asyncio.to_thread(self.provider.fetch_basic_info, code)
            warnings.extend(provider_warnings)
            if data:
                data["updated_at"] = datetime.utcnow()
                await db[self.basic_info_collection].update_one({"fund_code": code}, {"$set": data}, upsert=True)
                return {"exists": True, "stale": False, "refreshed": True, "warnings": warnings}
        except Exception as exc:
            warnings.append(f"基础资料刷新失败: {exc}")
            logger.warning("Refresh fund basic info failed: %s %s", code, exc, exc_info=True)
        cached_doc = await db[self.basic_info_collection].find_one({"fund_code": code}, {"_id": 1})
        exists = cached_doc is not None
        return {"exists": exists, "stale": exists, "refreshed": False, "warnings": warnings}

    async def _refresh_nav_history(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        warnings: List[str] = []
        try:
            records, provider_warnings = await asyncio.to_thread(self.provider.fetch_nav_history, code)
            warnings.extend(provider_warnings)
            now = datetime.utcnow()
            operations = []
            for record in records:
                record["updated_at"] = now
                operations.append(
                    UpdateOne(
                        {"fund_code": code, "nav_date": record["nav_date"]},
                        {"$set": record},
                        upsert=True,
                    )
                )
            if operations:
                await db[self.nav_history_collection].bulk_write(operations, ordered=False)
                return {"exists": True, "stale": False, "refreshed": True, "warnings": warnings}
        except Exception as exc:
            warnings.append(f"净值走势刷新失败: {exc}")
            logger.warning("Refresh fund nav history failed: %s %s", code, exc, exc_info=True)
        cached_doc = await db[self.nav_history_collection].find_one({"fund_code": code}, {"_id": 1})
        exists = cached_doc is not None
        return {"exists": exists, "stale": exists, "refreshed": False, "warnings": warnings}

    async def _refresh_performance(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        warnings: List[str] = []
        try:
            records, provider_warnings = await asyncio.to_thread(self.provider.fetch_performance, code)
            warnings.extend(provider_warnings)
            now = datetime.utcnow()
            operations = []
            for record in records:
                record["updated_at"] = now
                operations.append(
                    UpdateOne(
                        {
                            "fund_code": code,
                            "performance_type": record.get("performance_type"),
                            "period": record.get("period"),
                        },
                        {"$set": record},
                        upsert=True,
                    )
                )
            if operations:
                await db[self.performance_collection].bulk_write(operations, ordered=False)
                return {"exists": True, "stale": False, "refreshed": True, "warnings": warnings}
        except Exception as exc:
            warnings.append(f"阶段业绩刷新失败: {exc}")
            logger.warning("Refresh fund performance failed: %s %s", code, exc, exc_info=True)
        cached_doc = await db[self.performance_collection].find_one({"fund_code": code}, {"_id": 1})
        exists = cached_doc is not None
        return {"exists": exists, "stale": exists, "refreshed": False, "warnings": warnings}

    async def _refresh_fee_info(self, code: str) -> Dict[str, Any]:
        db = get_mongo_db()
        warnings: List[str] = []
        try:
            data, provider_warnings = await asyncio.to_thread(self.provider.fetch_fee_info, code)
            warnings.extend(provider_warnings)
            if data:
                data["updated_at"] = datetime.utcnow()
                await db[self.fee_info_collection].update_one({"fund_code": code}, {"$set": data}, upsert=True)
                return {"exists": True, "stale": False, "refreshed": True, "warnings": warnings}
        except Exception as exc:
            warnings.append(f"费用规则刷新失败: {exc}")
            logger.warning("Refresh fund fee info failed: %s %s", code, exc, exc_info=True)
        cached_doc = await db[self.fee_info_collection].find_one({"fund_code": code}, {"_id": 1})
        exists = cached_doc is not None
        return {"exists": exists, "stale": exists, "refreshed": False, "warnings": warnings}

    async def _refresh_holdings(self, code: str, year: Optional[str] = None) -> Dict[str, Any]:
        request_year = self._normalize_year(year)
        db = get_mongo_db()
        warnings: List[str] = []
        try:
            data, provider_warnings = await asyncio.to_thread(self.provider.fetch_holdings, code, request_year)
            warnings.extend(provider_warnings)
            if data and (
                data.get("asset_allocation")
                or data.get("stock_holdings")
                or data.get("bond_holdings")
            ):
                data["updated_at"] = datetime.utcnow()
                data["request_year"] = request_year
                await db[self.holdings_collection].update_one(
                    {"fund_code": code, "request_year": request_year},
                    {"$set": data},
                    upsert=True,
                )
                return {"exists": True, "stale": False, "refreshed": True, "warnings": warnings}
        except Exception as exc:
            warnings.append(f"Fund holdings refresh failed: {exc}")
            logger.warning("Refresh fund holdings failed: %s %s", code, exc, exc_info=True)

        cached_doc = await db[self.holdings_collection].find_one(
            {"fund_code": code, "request_year": request_year},
            {"_id": 1},
        )
        exists = cached_doc is not None
        return {"exists": exists, "stale": exists, "refreshed": False, "warnings": warnings}

    @staticmethod
    def _normalize_code(fund_code: str) -> str:
        code = str(fund_code or "").strip()
        return code.zfill(6) if code.isdigit() else code

    @staticmethod
    def _normalize_year(year: Optional[str] = None) -> str:
        text = str(year or datetime.utcnow().year).strip()
        return text if text.isdigit() and len(text) == 4 else str(datetime.utcnow().year)

    @staticmethod
    def _is_stale(updated_at: Any, ttl_hours: int) -> bool:
        if not updated_at:
            return True
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                return True
        return datetime.utcnow() - updated_at > timedelta(hours=ttl_hours)

    @staticmethod
    def _clean_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in doc.items():
            if key == "_id":
                continue
            result[key] = value
        return result

    @staticmethod
    def _period_start_date(period: str) -> Optional[str]:
        normalized = str(period or "1y").lower()
        now = datetime.utcnow().date()
        days_map = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "3y": 365 * 3,
        }
        if normalized in {"all", "max", "成立来"}:
            return None
        days = days_map.get(normalized, 365)
        return (now - timedelta(days=days)).isoformat()


_fund_data_service: Optional[FundDataService] = None


def get_fund_data_service() -> FundDataService:
    global _fund_data_service
    if _fund_data_service is None:
        _fund_data_service = FundDataService()
    return _fund_data_service
