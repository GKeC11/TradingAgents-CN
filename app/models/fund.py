"""
Fund query models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FundSearchItem(BaseModel):
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund short name")
    fund_type: Optional[str] = Field(None, description="Fund type")
    pinyin_abbr: Optional[str] = Field(None, description="Pinyin abbreviation")
    pinyin_full: Optional[str] = Field(None, description="Full pinyin")
    source: str = Field("akshare", description="Data source")
    updated_at: Optional[datetime] = Field(None, description="Update time")


class FundBasicInfo(BaseModel):
    fund_code: str
    fund_name: Optional[str] = None
    fund_full_name: Optional[str] = None
    fund_type: Optional[str] = None
    manager: Optional[str] = None
    management_company: Optional[str] = None
    custodian_bank: Optional[str] = None
    inception_date: Optional[str] = None
    asset_scale: Optional[str] = None
    benchmark: Optional[str] = None
    investment_objective: Optional[str] = None
    investment_strategy: Optional[str] = None
    rating: Optional[str] = None
    source: str = "akshare"
    updated_at: Optional[datetime] = None


class FundNavRecord(BaseModel):
    fund_code: str
    nav_date: str
    unit_nav: Optional[float] = None
    accumulated_nav: Optional[float] = None
    daily_return: Optional[float] = None
    source: str = "akshare"


class FundPerformanceItem(BaseModel):
    fund_code: str
    performance_type: Optional[str] = None
    period: Optional[str] = None
    return_rate: Optional[float] = None
    max_drawdown: Optional[float] = None
    rank: Optional[str] = None
    source: str = "akshare"
    updated_at: Optional[datetime] = None


class FundFeeInfo(BaseModel):
    fund_code: str
    purchase_status: Optional[str] = None
    redeem_status: Optional[str] = None
    fixed_investment_status: Optional[str] = None
    min_purchase_amount: Optional[str] = None
    management_fee: Optional[str] = None
    custody_fee: Optional[str] = None
    sales_service_fee: Optional[str] = None
    redeem_fee_rules: List[Dict[str, Any]] = Field(default_factory=list)
    raw_rules: Dict[str, Any] = Field(default_factory=dict)
    source: str = "akshare"
    updated_at: Optional[datetime] = None


class FundAssetAllocation(BaseModel):
    asset_type: str
    ratio: Optional[float] = None


class FundStockHolding(BaseModel):
    fund_code: str
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    ratio: Optional[float] = None
    shares: Optional[float] = None
    market_value: Optional[float] = None
    quarter: Optional[str] = None
    source: str = "akshare"


class FundBondHolding(BaseModel):
    fund_code: str
    bond_code: Optional[str] = None
    bond_name: Optional[str] = None
    ratio: Optional[float] = None
    market_value: Optional[float] = None
    quarter: Optional[str] = None
    source: str = "akshare"


class FundHoldingsResponse(BaseModel):
    fund_code: str
    request_year: Optional[str] = None
    report_year: Optional[str] = None
    allocation_date: Optional[str] = None
    asset_allocation: List[FundAssetAllocation] = Field(default_factory=list)
    stock_holdings: List[FundStockHolding] = Field(default_factory=list)
    bond_holdings: List[FundBondHolding] = Field(default_factory=list)
    stock_total_ratio: Optional[float] = None
    bond_total_ratio: Optional[float] = None
    source: str = "akshare"
    updated_at: Optional[datetime] = None


class FundDetailResponse(BaseModel):
    basic_info: Optional[FundBasicInfo] = None
    latest_nav: Optional[FundNavRecord] = None
    nav_history: List[FundNavRecord] = Field(default_factory=list)
    performance: List[FundPerformanceItem] = Field(default_factory=list)
    fee_info: Optional[FundFeeInfo] = None
    holdings: Optional[FundHoldingsResponse] = None
    data_warnings: List[str] = Field(default_factory=list)
    cache_status: Dict[str, Any] = Field(default_factory=dict)
