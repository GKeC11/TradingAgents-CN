export interface FundSearchItem {
  fund_code: string
  fund_name: string
  fund_type?: string
  pinyin_abbr?: string
  pinyin_full?: string
  source?: string
  updated_at?: string
}

export interface FundBasicInfo {
  fund_code: string
  fund_name?: string
  fund_full_name?: string
  fund_type?: string
  manager?: string
  management_company?: string
  custodian_bank?: string
  inception_date?: string
  asset_scale?: string
  benchmark?: string
  investment_objective?: string
  investment_strategy?: string
  rating?: string
  source?: string
  updated_at?: string
}

export interface FundNavRecord {
  fund_code: string
  nav_date: string
  unit_nav?: number
  accumulated_nav?: number
  daily_return?: number
  source?: string
  updated_at?: string
}

export interface FundPerformanceItem {
  fund_code: string
  performance_type?: string
  period?: string
  return_rate?: number
  max_drawdown?: number
  rank?: string
  source?: string
  updated_at?: string
}

export interface FundFeeInfo {
  fund_code: string
  purchase_status?: string
  redeem_status?: string
  fixed_investment_status?: string
  min_purchase_amount?: string
  management_fee?: string
  custody_fee?: string
  sales_service_fee?: string
  redeem_fee_rules?: Array<Record<string, any>>
  raw_rules?: Record<string, any>
  source?: string
  updated_at?: string
}

export interface FundAssetAllocation {
  asset_type: string
  ratio?: number
}

export interface FundStockHolding {
  fund_code: string
  stock_code?: string
  stock_name?: string
  ratio?: number
  shares?: number
  market_value?: number
  quarter?: string
  source?: string
}

export interface FundBondHolding {
  fund_code: string
  bond_code?: string
  bond_name?: string
  ratio?: number
  market_value?: number
  quarter?: string
  source?: string
}

export interface FundHoldings {
  fund_code: string
  request_year?: string
  report_year?: string
  allocation_date?: string
  asset_allocation: FundAssetAllocation[]
  stock_holdings: FundStockHolding[]
  bond_holdings: FundBondHolding[]
  stock_total_ratio?: number
  bond_total_ratio?: number
  source?: string
  updated_at?: string
}

export interface FundCacheStatus {
  exists?: boolean
  stale?: boolean
  refreshed?: boolean
  count?: number
  latest_updated_at?: string
}

export interface FundSearchResponse {
  items: FundSearchItem[]
  total: number
  query: string
  cache_status?: FundCacheStatus
  data_warnings?: string[]
}

export interface FundDetailResponse {
  basic_info?: FundBasicInfo | null
  latest_nav?: FundNavRecord | null
  nav_history: FundNavRecord[]
  performance: FundPerformanceItem[]
  fee_info?: FundFeeInfo | null
  holdings?: FundHoldings | null
  data_warnings?: string[]
  cache_status?: Record<string, FundCacheStatus>
}

export interface FundNavResponse {
  fund_code: string
  period: string
  items: FundNavRecord[]
  cache_status?: FundCacheStatus
  data_warnings?: string[]
}

export interface FundHoldingsResponse {
  fund_code: string
  request_year: string
  holdings?: FundHoldings | null
  cache_status?: FundCacheStatus
  data_warnings?: string[]
}
