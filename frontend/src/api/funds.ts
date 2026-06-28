import { ApiClient } from './request'
import type { FundDetailResponse, FundHoldingsResponse, FundNavResponse, FundSearchResponse } from '@/types/fund'

export const fundsApi = {
  async searchFunds(query: string, limit = 20) {
    return ApiClient.get<FundSearchResponse>('/api/funds/search', { query, limit })
  },

  async getFundDetail(fundCode: string) {
    return ApiClient.get<FundDetailResponse>(`/api/funds/${fundCode}`)
  },

  async getFundNav(fundCode: string, period = '1y') {
    return ApiClient.get<FundNavResponse>(`/api/funds/${fundCode}/nav`, { period })
  },

  async getFundHoldings(fundCode: string, year?: string) {
    return ApiClient.get<FundHoldingsResponse>(`/api/funds/${fundCode}/holdings`, { year })
  },

  async refreshFund(fundCode: string) {
    return ApiClient.post<FundDetailResponse>(`/api/funds/${fundCode}/refresh`)
  }
}
