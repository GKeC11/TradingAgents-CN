<template>
  <div class="fund-detail-page">
    <div class="page-header">
      <div>
        <div class="code">{{ fundCode }}</div>
        <h1>{{ basicInfo?.fund_name || '-' }}</h1>
        <div class="meta">
          <el-tag v-if="basicInfo?.fund_type" size="small">{{ basicInfo.fund_type }}</el-tag>
          <el-tag v-if="basicInfo?.source" size="small" type="info">{{ basicInfo.source }}</el-tag>
        </div>
      </div>
      <div class="actions">
        <el-button @click="router.push('/funds/search')">返回搜索</el-button>
        <el-button type="primary" :icon="Refresh" :loading="refreshing" @click="refreshFund">刷新</el-button>
      </div>
    </div>

    <el-alert
      v-if="warnings.length"
      type="warning"
      :closable="false"
      class="warning"
    >
      <template #title>{{ warnings.join('；') }}</template>
    </el-alert>

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else>
      <el-row :gutter="16">
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="info-card">
            <template #header>基础资料</template>
            <div class="kv-list">
              <div v-for="item in basicRows" :key="item.label" class="kv-item">
                <span>{{ item.label }}</span>
                <b>{{ item.value || '-' }}</b>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="info-card">
            <template #header>最新净值</template>
            <div class="nav-value">{{ formatNumber(latestNav?.unit_nav) }}</div>
            <div class="nav-date">{{ latestNav?.nav_date || '-' }}</div>
            <div class="kv-list compact">
              <div class="kv-item">
                <span>累计净值</span>
                <b>{{ formatNumber(latestNav?.accumulated_nav) }}</b>
              </div>
              <div class="kv-item">
                <span>日增长率</span>
                <b :class="returnClass(latestNav?.daily_return)">{{ formatPercent(latestNav?.daily_return) }}</b>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="info-card">
            <template #header>交易费用</template>
            <div class="kv-list">
              <div v-for="item in feeRows" :key="item.label" class="kv-item">
                <span>{{ item.label }}</span>
                <b>{{ item.value || '-' }}</b>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span>持仓披露</span>
            <div class="header-tags">
              <el-tag v-if="holdings?.allocation_date" size="small" type="info">
                {{ holdings.allocation_date }}
              </el-tag>
              <el-tag v-if="holdings?.report_year" size="small" type="info">
                {{ holdings.report_year }}
              </el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="16">
          <el-col :xs="24" :lg="8">
            <div class="sub-title">资产配置</div>
            <el-table :data="assetAllocation" empty-text="暂无资产配置">
              <el-table-column prop="asset_type" label="资产类型" />
              <el-table-column label="仓位占比" width="120">
                <template #default="{ row }">{{ formatPercent(row.ratio) }}</template>
              </el-table-column>
            </el-table>
          </el-col>

          <el-col :xs="24" :lg="16">
            <div class="sub-title">
              股票持仓
              <span v-if="holdings?.stock_total_ratio">合计 {{ formatPercent(holdings.stock_total_ratio) }}</span>
            </div>
            <el-table :data="stockHoldings" max-height="320" empty-text="暂无股票持仓">
              <el-table-column prop="stock_code" label="代码" width="110" />
              <el-table-column prop="stock_name" label="名称" min-width="130" />
              <el-table-column label="占净值" width="110">
                <template #default="{ row }">{{ formatPercent(row.ratio) }}</template>
              </el-table-column>
              <el-table-column label="持仓市值" width="120">
                <template #default="{ row }">{{ formatAmount(row.market_value) }}</template>
              </el-table-column>
              <el-table-column prop="quarter" label="季度" min-width="170" />
            </el-table>
          </el-col>
        </el-row>

        <div class="sub-title bond-title">
          债券持仓
          <span v-if="holdings?.bond_total_ratio">合计 {{ formatPercent(holdings.bond_total_ratio) }}</span>
        </div>
        <el-table :data="bondHoldings" max-height="320" empty-text="暂无债券持仓">
          <el-table-column prop="bond_code" label="代码" width="130" />
          <el-table-column prop="bond_name" label="名称" min-width="220" />
          <el-table-column label="占净值" width="110">
            <template #default="{ row }">{{ formatPercent(row.ratio) }}</template>
          </el-table-column>
          <el-table-column label="持仓市值" width="120">
            <template #default="{ row }">{{ formatAmount(row.market_value) }}</template>
          </el-table-column>
          <el-table-column prop="quarter" label="季度" min-width="180" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span>阶段业绩</span>
            <el-tag size="small" type="info">{{ performance.length }} 条</el-tag>
          </div>
        </template>
        <el-table :data="performance" empty-text="暂无阶段业绩">
          <el-table-column prop="performance_type" label="类型" width="110" />
          <el-table-column prop="period" label="周期" width="120" />
          <el-table-column label="区间收益" width="130">
            <template #default="{ row }">
              <span :class="returnClass(row.return_rate)">{{ formatPercent(row.return_rate) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="最大回撤" width="130">
            <template #default="{ row }">{{ formatPercent(row.max_drawdown) }}</template>
          </el-table-column>
          <el-table-column prop="rank" label="同类排名" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span>净值走势</span>
            <el-segmented v-model="navPeriod" :options="periodOptions" size="small" @change="loadNav" />
          </div>
        </template>
        <el-table :data="navHistory" max-height="420" empty-text="暂无净值数据">
          <el-table-column prop="nav_date" label="日期" width="130" />
          <el-table-column label="单位净值" width="130">
            <template #default="{ row }">{{ formatNumber(row.unit_nav) }}</template>
          </el-table-column>
          <el-table-column label="累计净值" width="130">
            <template #default="{ row }">{{ formatNumber(row.accumulated_nav) }}</template>
          </el-table-column>
          <el-table-column label="日增长率">
            <template #default="{ row }">
              <span :class="returnClass(row.daily_return)">{{ formatPercent(row.daily_return) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { fundsApi } from '@/api/funds'
import type {
  FundBasicInfo,
  FundDetailResponse,
  FundFeeInfo,
  FundHoldings,
  FundNavRecord,
  FundPerformanceItem
} from '@/types/fund'

const route = useRoute()
const router = useRouter()

const fundCode = computed(() => String(route.params.code || '').trim())
const loading = ref(false)
const refreshing = ref(false)
const detail = ref<FundDetailResponse | null>(null)
const navHistory = ref<FundNavRecord[]>([])
const navPeriod = ref('1y')
const periodOptions = [
  { label: '1月', value: '1m' },
  { label: '3月', value: '3m' },
  { label: '6月', value: '6m' },
  { label: '1年', value: '1y' },
  { label: '全部', value: 'all' }
]

const basicInfo = computed<FundBasicInfo | null>(() => detail.value?.basic_info || null)
const latestNav = computed<FundNavRecord | null>(() => detail.value?.latest_nav || null)
const performance = computed<FundPerformanceItem[]>(() => detail.value?.performance || [])
const feeInfo = computed<FundFeeInfo | null>(() => detail.value?.fee_info || null)
const holdings = computed<FundHoldings | null>(() => detail.value?.holdings || null)
const assetAllocation = computed(() => holdings.value?.asset_allocation || [])
const stockHoldings = computed(() => holdings.value?.stock_holdings || [])
const bondHoldings = computed(() => holdings.value?.bond_holdings || [])
const warnings = computed(() => detail.value?.data_warnings || [])

const basicRows = computed(() => [
  { label: '基金全称', value: basicInfo.value?.fund_full_name },
  { label: '基金公司', value: basicInfo.value?.management_company },
  { label: '基金经理', value: basicInfo.value?.manager },
  { label: '托管银行', value: basicInfo.value?.custodian_bank },
  { label: '成立日期', value: basicInfo.value?.inception_date },
  { label: '最新规模', value: basicInfo.value?.asset_scale },
  { label: '基金评级', value: basicInfo.value?.rating },
  { label: '业绩基准', value: basicInfo.value?.benchmark }
])

const feeRows = computed(() => [
  { label: '申购状态', value: feeInfo.value?.purchase_status },
  { label: '赎回状态', value: feeInfo.value?.redeem_status },
  { label: '定投状态', value: feeInfo.value?.fixed_investment_status },
  { label: '申购起点', value: feeInfo.value?.min_purchase_amount },
  { label: '管理费率', value: feeInfo.value?.management_fee },
  { label: '托管费率', value: feeInfo.value?.custody_fee },
  { label: '销售服务费率', value: feeInfo.value?.sales_service_fee }
])

const loadDetail = async () => {
  if (!fundCode.value) return
  loading.value = true
  try {
    const res = await fundsApi.getFundDetail(fundCode.value)
    detail.value = res.data
    navHistory.value = res.data?.nav_history || []
  } catch (error: any) {
    detail.value = null
    navHistory.value = []
    ElMessage.error(error?.message || '基金详情加载失败')
  } finally {
    loading.value = false
  }
}

const loadNav = async () => {
  if (!fundCode.value) return
  try {
    const res = await fundsApi.getFundNav(fundCode.value, navPeriod.value)
    navHistory.value = res.data?.items || []
  } catch (error: any) {
    ElMessage.error(error?.message || '净值数据加载失败')
  }
}

const refreshFund = async () => {
  if (!fundCode.value) return
  refreshing.value = true
  try {
    const res = await fundsApi.refreshFund(fundCode.value)
    detail.value = res.data
    navHistory.value = res.data?.nav_history || []
    ElMessage.success('基金缓存已刷新')
  } catch (error: any) {
    ElMessage.error(error?.message || '基金刷新失败')
  } finally {
    refreshing.value = false
  }
}

const formatNumber = (value?: number | null) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
  return value.toFixed(4)
}

const formatPercent = (value?: number | null) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
  return `${value.toFixed(2)}%`
}

const formatAmount = (value?: number | null) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '-'
  if (Math.abs(value) >= 10000) return `${(value / 10000).toFixed(2)}亿`
  return `${value.toFixed(2)}万`
}

const returnClass = (value?: number | null) => {
  if (typeof value !== 'number') return ''
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}

watch(() => route.params.code, () => {
  void loadDetail()
})

onMounted(() => {
  void loadDetail()
})
</script>

<style scoped lang="scss">
.fund-detail-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;

  .code {
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }

  h1 {
    margin: 4px 0 8px;
    font-size: 24px;
    font-weight: 700;
  }

  .meta,
  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}

.warning {
  margin-bottom: 16px;
}

.info-card,
.section-card {
  border-radius: 8px;
}

.info-card {
  min-height: 260px;
  margin-bottom: 16px;
}

.section-card {
  margin-top: 16px;
}

.kv-list {
  display: grid;
  gap: 12px;

  &.compact {
    margin-top: 20px;
  }
}

.kv-item {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 12px;
  align-items: start;

  span {
    color: var(--el-text-color-secondary);
  }

  b {
    font-weight: 600;
    word-break: break-word;
  }
}

.nav-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.nav-date {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sub-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin: 4px 0 10px;
  font-size: 14px;
  font-weight: 600;

  span {
    color: var(--el-text-color-secondary);
    font-weight: 400;
  }
}

.bond-title {
  margin-top: 18px;
}

.positive {
  color: var(--el-color-danger);
}

.negative {
  color: var(--el-color-success);
}

@media (max-width: 768px) {
  .fund-detail-page {
    padding: 16px;
  }

  .page-header {
    display: grid;
  }

  .card-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
