<template>
  <div class="fund-search-page">
    <div class="page-header">
      <div>
        <h1>基金分析</h1>
        <p>基金查询</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="runSearch(true)">刷新</el-button>
    </div>

    <el-card shadow="never" class="search-panel">
      <div class="search-row">
        <el-input
          v-model="keyword"
          size="large"
          clearable
          placeholder="基金代码、名称或拼音"
          @input="scheduleSearch"
          @keyup.enter="runSearch(true)"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" :loading="loading" @click="runSearch(true)">
          查询
        </el-button>
      </div>
    </el-card>

    <el-alert
      v-if="warnings.length"
      type="warning"
      :closable="false"
      class="warning"
    >
      <template #title>
        {{ warnings.join('；') }}
      </template>
    </el-alert>

    <el-card shadow="never" class="result-panel">
      <template #header>
        <div class="card-header">
          <span>查询结果</span>
          <el-tag v-if="cacheText" size="small" type="info">{{ cacheText }}</el-tag>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="items"
        row-key="fund_code"
        empty-text="暂无基金数据"
        @row-click="openFund"
      >
        <el-table-column prop="fund_code" label="代码" width="120" />
        <el-table-column prop="fund_name" label="名称" min-width="220" />
        <el-table-column prop="fund_type" label="类型" min-width="150" />
        <el-table-column prop="pinyin_abbr" label="拼音缩写" min-width="150" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="openFund(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && searched && items.length === 0" description="没有匹配的基金" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { fundsApi } from '@/api/funds'
import type { FundSearchItem } from '@/types/fund'

const route = useRoute()
const router = useRouter()

const keyword = ref(String(route.query.q || ''))
const items = ref<FundSearchItem[]>([])
const warnings = ref<string[]>([])
const loading = ref(false)
const searched = ref(false)
const cacheStatus = ref<Record<string, any> | null>(null)
let timer: ReturnType<typeof setTimeout> | null = null
let requestSeq = 0

const cacheText = computed(() => {
  const status = cacheStatus.value
  if (!status) return ''
  if (status.stale) return '缓存已过期'
  if (status.refreshed) return '已刷新'
  if (typeof status.count === 'number') return `索引 ${status.count} 条`
  return ''
})

const scheduleSearch = () => {
  if (timer) {
    clearTimeout(timer)
  }
  timer = setTimeout(() => {
    void runSearch(false)
  }, 350)
}

const runSearch = async (manual: boolean) => {
  const query = keyword.value.trim()
  if (!query && !manual) {
    items.value = []
    warnings.value = []
    searched.value = false
    return
  }

  const seq = ++requestSeq
  loading.value = true
  searched.value = true
  try {
    const res = await fundsApi.searchFunds(query, 20)
    if (seq !== requestSeq) return
    const data = res.data
    items.value = data?.items || []
    warnings.value = data?.data_warnings || []
    cacheStatus.value = data?.cache_status || null
    if (query) {
      void router.replace({ path: '/funds/search', query: { q: query } })
    }
  } catch (error: any) {
    if (seq !== requestSeq) return
    items.value = []
    warnings.value = []
    ElMessage.error(error?.message || '基金查询失败')
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

const openFund = (fund: FundSearchItem) => {
  router.push(`/funds/${fund.fund_code}`)
}

onMounted(() => {
  if (keyword.value.trim()) {
    void runSearch(false)
  }
})

onBeforeUnmount(() => {
  if (timer) {
    clearTimeout(timer)
  }
})
</script>

<style scoped lang="scss">
.fund-search-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
  }

  p {
    margin: 6px 0 0;
    color: var(--el-text-color-secondary);
  }
}

.search-panel,
.result-panel {
  border-radius: 8px;
}

.search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.warning {
  margin: 16px 0;
}

.result-panel {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table__row) {
  cursor: pointer;
}

@media (max-width: 768px) {
  .fund-search-page {
    padding: 16px;
  }

  .page-header,
  .search-row {
    grid-template-columns: 1fr;
  }

  .page-header {
    display: grid;
    gap: 12px;
    align-items: start;
  }
}
</style>
