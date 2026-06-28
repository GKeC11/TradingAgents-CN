"""
China public fund data provider based on AkShare.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class ChinaFundProvider:
    """Standardized fund data provider for China public funds."""

    source = "akshare"

    def __init__(self):
        import akshare as ak

        self.ak = ak

    def fetch_fund_list(self) -> List[Dict[str, Any]]:
        df = self.ak.fund_name_em()
        result: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            result.append({
                "fund_code": self._clean_code(self._row_value(row, "基金代码", 0)),
                "pinyin_abbr": self._clean_str(self._row_value(row, "拼音缩写", 1)),
                "fund_name": self._clean_str(self._row_value(row, "基金简称", 2)),
                "fund_type": self._clean_str(self._row_value(row, "基金类型", 3)),
                "pinyin_full": self._clean_str(self._row_value(row, "拼音全称", 4)),
                "source": self.source,
            })

        return [item for item in result if item["fund_code"] and item["fund_name"]]

    def fetch_basic_info(self, fund_code: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        warnings: List[str] = []
        code = self._clean_code(fund_code)

        try:
            df = self.ak.fund_individual_basic_info_xq(symbol=code, timeout=15)
        except Exception as exc:
            logger.warning("Fetch fund basic info failed: %s %s", code, exc)
            return None, [f"基础资料获取失败: {exc}"]

        values = self._item_value_map(df)
        if not values:
            return None, ["基础资料为空"]

        return {
            "fund_code": code,
            "fund_name": values.get("基金名称"),
            "fund_full_name": values.get("基金全称"),
            "fund_type": values.get("基金类型"),
            "manager": values.get("基金经理"),
            "management_company": values.get("基金公司"),
            "custodian_bank": values.get("托管银行"),
            "inception_date": values.get("成立时间"),
            "asset_scale": values.get("最新规模"),
            "benchmark": values.get("业绩比较基准"),
            "investment_objective": values.get("投资目标"),
            "investment_strategy": values.get("投资策略"),
            "rating": values.get("基金评级") or values.get("评级机构"),
            "source": self.source,
        }, warnings

    def fetch_nav_history(self, fund_code: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        warnings: List[str] = []
        code = self._clean_code(fund_code)
        unit_df: Optional[pd.DataFrame] = None
        acc_df: Optional[pd.DataFrame] = None

        try:
            unit_df = self.ak.fund_open_fund_info_em(
                symbol=code,
                indicator="单位净值走势",
                period="成立来",
            )
        except Exception as exc:
            warnings.append(f"单位净值走势获取失败: {exc}")

        try:
            acc_df = self.ak.fund_open_fund_info_em(
                symbol=code,
                indicator="累计净值走势",
                period="成立来",
            )
        except Exception as exc:
            warnings.append(f"累计净值走势获取失败: {exc}")

        if unit_df is None or unit_df.empty:
            return [], warnings or ["净值走势为空"]

        unit_records: Dict[str, Dict[str, Any]] = {}
        date_col = self._first_column(unit_df, "净值日期", 0)
        unit_col = self._first_column(unit_df, "单位净值", 1)
        daily_col = self._first_column(unit_df, "日增长率", 2)

        for _, row in unit_df.iterrows():
            nav_date = self._date_str(row.get(date_col))
            if not nav_date:
                continue
            unit_records[nav_date] = {
                "fund_code": code,
                "nav_date": nav_date,
                "unit_nav": self._to_float(row.get(unit_col)),
                "accumulated_nav": None,
                "daily_return": self._to_float(row.get(daily_col)),
                "source": self.source,
            }

        if acc_df is not None and not acc_df.empty:
            acc_date_col = self._first_column(acc_df, "净值日期", 0)
            acc_col = self._first_column(acc_df, "累计净值", 1)
            for _, row in acc_df.iterrows():
                nav_date = self._date_str(row.get(acc_date_col))
                if nav_date and nav_date in unit_records:
                    unit_records[nav_date]["accumulated_nav"] = self._to_float(row.get(acc_col))

        return [unit_records[key] for key in sorted(unit_records)], warnings

    def fetch_performance(self, fund_code: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        code = self._clean_code(fund_code)
        try:
            df = self.ak.fund_individual_achievement_xq(symbol=code, timeout=15)
        except Exception as exc:
            logger.warning("Fetch fund performance failed: %s %s", code, exc)
            return [], [f"阶段业绩获取失败: {exc}"]

        records: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "fund_code": code,
                "performance_type": self._clean_str(self._row_value(row, "业绩类型", 0)),
                "period": self._clean_str(self._row_value(row, "周期", 1)),
                "return_rate": self._to_float(self._row_value(row, "本产品区间收益", 2)),
                "max_drawdown": self._to_float(self._row_value(row, "本产品最大回撒", 3)),
                "rank": self._clean_str(self._row_value(row, "周期收益同类排名", 4)),
                "source": self.source,
            })

        return records, []

    def fetch_fee_info(self, fund_code: str) -> Tuple[Dict[str, Any], List[str]]:
        code = self._clean_code(fund_code)
        warnings: List[str] = []
        info: Dict[str, Any] = {
            "fund_code": code,
            "purchase_status": None,
            "redeem_status": None,
            "fixed_investment_status": None,
            "min_purchase_amount": None,
            "management_fee": None,
            "custody_fee": None,
            "sales_service_fee": None,
            "redeem_fee_rules": [],
            "raw_rules": {},
            "source": self.source,
        }

        self._merge_fee_table(code, "交易状态", info, warnings)
        self._merge_fee_table(code, "申购与赎回金额", info, warnings)
        self._merge_fee_table(code, "运作费用", info, warnings)
        self._merge_fee_table(code, "赎回费率", info, warnings)

        try:
            detail_df = self.ak.fund_individual_detail_info_xq(symbol=code, timeout=15)
            if detail_df is not None and not detail_df.empty:
                info["raw_rules"]["detail_rules"] = self._records(detail_df)
        except Exception as exc:
            warnings.append(f"交易规则详情获取失败: {exc}")

        return info, warnings

    def fetch_holdings(self, fund_code: str, year: Optional[str] = None) -> Tuple[Dict[str, Any], List[str]]:
        code = self._clean_code(fund_code)
        request_year = str(year or datetime.utcnow().year)
        warnings: List[str] = []

        asset_allocation, allocation_date, allocation_warnings = self._fetch_asset_allocation(code, request_year)
        warnings.extend(allocation_warnings)

        stock_records, stock_year, stock_warnings = self._fetch_stock_holdings(code, request_year)
        warnings.extend(stock_warnings)

        bond_records, bond_year, bond_warnings = self._fetch_bond_holdings(code, request_year)
        warnings.extend(bond_warnings)

        report_year = stock_year or bond_year or request_year
        stock_total_ratio = round(sum(item.get("ratio") or 0 for item in stock_records), 4) if stock_records else None
        bond_total_ratio = round(sum(item.get("ratio") or 0 for item in bond_records), 4) if bond_records else None

        return {
            "fund_code": code,
            "request_year": request_year,
            "report_year": report_year,
            "allocation_date": allocation_date,
            "asset_allocation": asset_allocation,
            "stock_holdings": stock_records,
            "bond_holdings": bond_records,
            "stock_total_ratio": stock_total_ratio,
            "bond_total_ratio": bond_total_ratio,
            "source": self.source,
        }, warnings

    def _fetch_asset_allocation(self, code: str, request_year: str) -> Tuple[List[Dict[str, Any]], Optional[str], List[str]]:
        warnings: List[str] = []
        for report_date in self._asset_allocation_dates(request_year):
            try:
                df = self.ak.fund_individual_detail_hold_xq(symbol=code, date=report_date, timeout=15)
            except Exception as exc:
                warnings.append(f"Asset allocation fetch failed for {report_date}: {exc}")
                continue

            if df is None or df.empty:
                continue

            records: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                asset_type = self._clean_str(self._row_value(row, "资产类型", 0))
                ratio = self._to_float(self._row_value(row, "仓位占比", 1))
                if asset_type:
                    records.append({
                        "asset_type": asset_type,
                        "ratio": ratio,
                    })
            if records:
                return records, self._format_report_date(report_date), warnings

        return [], None, warnings

    def _fetch_stock_holdings(self, code: str, request_year: str) -> Tuple[List[Dict[str, Any]], Optional[str], List[str]]:
        warnings: List[str] = []
        for query_year in self._holding_years(request_year):
            try:
                df = self.ak.fund_portfolio_hold_em(symbol=code, date=query_year)
            except Exception as exc:
                warnings.append(f"Stock holdings fetch failed for {query_year}: {exc}")
                continue

            if df is None or df.empty:
                continue

            records: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                records.append({
                    "fund_code": code,
                    "stock_code": self._clean_str(self._row_value(row, "股票代码", 1)),
                    "stock_name": self._clean_str(self._row_value(row, "股票名称", 2)),
                    "ratio": self._to_float(self._row_value(row, "占净值比例", 3)),
                    "shares": self._to_float(self._row_value(row, "持股数", 4)),
                    "market_value": self._to_float(self._row_value(row, "持仓市值", 5)),
                    "quarter": self._clean_str(self._row_value(row, "季度", 6)),
                    "source": self.source,
                })
            records = self._latest_quarter_records(records)
            if records:
                return records, query_year, warnings

        return [], None, warnings

    def _fetch_bond_holdings(self, code: str, request_year: str) -> Tuple[List[Dict[str, Any]], Optional[str], List[str]]:
        warnings: List[str] = []
        for query_year in self._holding_years(request_year):
            try:
                df = self.ak.fund_portfolio_bond_hold_em(symbol=code, date=query_year)
            except Exception as exc:
                warnings.append(f"Bond holdings fetch failed for {query_year}: {exc}")
                continue

            if df is None or df.empty:
                continue

            records: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                records.append({
                    "fund_code": code,
                    "bond_code": self._clean_str(self._row_value(row, "债券代码", 1)),
                    "bond_name": self._clean_str(self._row_value(row, "债券名称", 2)),
                    "ratio": self._to_float(self._row_value(row, "占净值比例", 3)),
                    "market_value": self._to_float(self._row_value(row, "持仓市值", 4)),
                    "quarter": self._clean_str(self._row_value(row, "季度", 5)),
                    "source": self.source,
                })
            records = self._latest_quarter_records(records)
            if records:
                return records, query_year, warnings

        return [], None, warnings

    def _merge_fee_table(
        self,
        code: str,
        indicator: str,
        info: Dict[str, Any],
        warnings: List[str],
    ) -> None:
        try:
            df = self.ak.fund_fee_em(symbol=code, indicator=indicator)
        except Exception as exc:
            warnings.append(f"{indicator}获取失败: {exc}")
            return

        if df is None or df.empty:
            info["raw_rules"][indicator] = []
            return

        info["raw_rules"][indicator] = self._records(df)

        if indicator in {"交易状态", "申购与赎回金额", "运作费用"}:
            pairs = self._flat_pairs(df)
            if indicator == "交易状态":
                info["purchase_status"] = pairs.get("申购状态") or info["purchase_status"]
                info["redeem_status"] = pairs.get("赎回状态") or info["redeem_status"]
                info["fixed_investment_status"] = pairs.get("定投状态") or info["fixed_investment_status"]
            elif indicator == "申购与赎回金额":
                info["min_purchase_amount"] = pairs.get("申购起点") or pairs.get("首次购买") or info["min_purchase_amount"]
            elif indicator == "运作费用":
                info["management_fee"] = pairs.get("管理费率") or info["management_fee"]
                info["custody_fee"] = pairs.get("托管费率") or info["custody_fee"]
                info["sales_service_fee"] = pairs.get("销售服务费率") or info["sales_service_fee"]

        if indicator == "赎回费率":
            info["redeem_fee_rules"] = self._records(df)

    @staticmethod
    def _holding_years(request_year: str) -> List[str]:
        try:
            year = int(request_year)
        except ValueError:
            year = datetime.utcnow().year
        return [str(year), str(year - 1)]

    @staticmethod
    def _asset_allocation_dates(request_year: str) -> List[str]:
        try:
            year = int(request_year)
        except ValueError:
            year = datetime.utcnow().year

        today = datetime.utcnow().date()
        dates: List[str] = []
        if year < today.year:
            dates.extend([f"{year}1231", f"{year}0930", f"{year}0630", f"{year}0331"])
        else:
            if today.month >= 10:
                dates.append(f"{year}0930")
            if today.month >= 7:
                dates.append(f"{year}0630")
            if today.month >= 4:
                dates.append(f"{year}0331")
            dates.append(f"{year - 1}1231")
        dates.extend([f"{year - 1}0930", f"{year - 1}0630", f"{year - 1}0331"])
        return list(dict.fromkeys(dates))

    @staticmethod
    def _format_report_date(value: str) -> str:
        text = str(value or "")
        if len(text) == 8 and text.isdigit():
            return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
        return text

    @staticmethod
    def _latest_quarter_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not records:
            return []

        def quarter_key(item: Dict[str, Any]) -> Tuple[int, int]:
            text = str(item.get("quarter") or "")
            match = re.search(r"(\d{4}).*?([1-4])\s*季", text)
            if not match:
                return (0, 0)
            return (int(match.group(1)), int(match.group(2)))

        latest = max(quarter_key(item) for item in records)
        if latest == (0, 0):
            return records
        return [item for item in records if quarter_key(item) == latest]

    @staticmethod
    def _clean_code(value: Any) -> str:
        text = ChinaFundProvider._clean_str(value)
        if text and text.isdigit():
            return text.zfill(6)
        return text

    @staticmethod
    def _clean_str(value: Any) -> str:
        if value is None:
            return ""
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace("%", "").replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null", "<na>"}:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _date_str(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        try:
            return pd.to_datetime(value).date().isoformat()
        except Exception:
            return str(value).strip()

    @staticmethod
    def _row_value(row: pd.Series, name: str, index: int) -> Any:
        if name in row.index:
            return row[name]
        if len(row.index) > index:
            return row.iloc[index]
        return None

    @staticmethod
    def _first_column(df: pd.DataFrame, name: str, index: int) -> str:
        if name in df.columns:
            return name
        return str(df.columns[index])

    @classmethod
    def _item_value_map(cls, df: pd.DataFrame) -> Dict[str, str]:
        if df is None or df.empty:
            return {}
        result: Dict[str, str] = {}
        item_col = cls._first_column(df, "item", 0)
        value_col = cls._first_column(df, "value", 1)
        for _, row in df.iterrows():
            key = cls._clean_str(row.get(item_col))
            value = cls._clean_str(row.get(value_col))
            if key:
                result[key] = value
        return result

    @classmethod
    def _records(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            item: Dict[str, Any] = {}
            for column in df.columns:
                value = row.get(column)
                if value is None or pd.isna(value):
                    item[str(column)] = None
                else:
                    item[str(column)] = value.item() if hasattr(value, "item") else value
            records.append(item)
        return records

    @classmethod
    def _flat_pairs(cls, df: pd.DataFrame) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for _, row in df.iterrows():
            values = [cls._clean_str(row.get(col)) for col in df.columns]
            for idx in range(0, len(values) - 1, 2):
                if values[idx]:
                    pairs[values[idx]] = values[idx + 1]
        return pairs
