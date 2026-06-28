# TradingAgents 基金查询实现方案

## 1. 目标、原则和当前第一版范围

当前第一版目标是在现有 TradingAgents-CN 前后端分离架构上增加“稳定、快速查询基金”的能力。用户从左侧“基金分析”入口进入后，可以按基金代码、基金名称或拼音搜索基金，查看基金基础资料、最新净值、净值走势、阶段业绩、交易状态和费用规则。

当前优先级：高。该能力是基金扩展的前置能力，优先级高于基金分析任务、基金买卖建议和基金报告生成。只有基金查询链路稳定后，才继续推进分析和建议能力。

第一版以中国公募基金、ETF 联接基金和常见开放式基金为主，优先复用现有 `FastAPI + MongoDB + Vue 3 + Element Plus`、登录鉴权、前端路由和统一 API 请求能力。股票分析功能保持兼容，不修改现有股票分析、任务中心和报告中心流程。

当前第一版必须能跑通已验证样例 `012630`，并把 `014767` 作为新增查询验证样例。基金查询接口需要做到缓存命中时快速返回，缓存缺失或过期时按需拉取并写入 MongoDB。数据源局部失败时返回可用数据和明确提示，不让页面直接进入 500 或空白状态。

当前第一版不实现基金分析任务、基金买卖建议、基金报告生成、基金组合调仓、真实申购赎回和自动交易。页面可以保留“基金分析”命名，但第一版实际交付是基金查询基础能力。

## 2. 模块归属、依赖和代码结构

基金查询数据归属后端基金数据服务，基金数据源适配归属 `tradingagents.dataflows.providers.china`，基金页面归属前端业务页面。数据源适配层只负责采集和标准化基金数据，不生成投资结论；前端只调用后端 API，不直接调用 AkShare。

当前实现需要的依赖：

- `akshare>=1.17.86`：已有依赖，第一版作为基金数据主来源。
- `MongoDB`：保存基金基础信息、净值、持仓、分析任务和报告。
- 现有登录鉴权：基金查询接口沿用当前 Bearer Token 校验。

`akshare==1.18.64` 已用 `012630` 做过前置验证，当前第一版按以下接口落地 provider 契约：

- `fund_name_em()`：基金搜索和基金代码、简称、类型映射。
- `fund_individual_basic_info_xq(symbol)`：基金基础资料、基金公司、基金经理、规模、投资目标和业绩比较基准。
- `fund_open_fund_info_em(symbol, "单位净值走势", "成立来")`：单位净值和日增长率序列。
- `fund_open_fund_info_em(symbol, "累计净值走势", "成立来")`：累计净值序列。
- `fund_individual_achievement_xq(symbol)`：阶段收益、年度收益、最大回撤和同类排名。
- `fund_individual_detail_info_xq(symbol)` 与 `fund_fee_em(symbol, indicator)`：交易规则、管理费、托管费、销售服务费、赎回费和交易状态。

目标代码结构：

```text
app/
  models/
    fund.py
  routers/
    funds.py
  services/
    fund_data_service.py

tradingagents/
  dataflows/
    providers/
      china/
        fund.py

frontend/src/
  api/
    funds.ts
  types/
    fund.ts
  views/
    Funds/
      FundSearch.vue
      FundDetail.vue
```

现有文件需要最小改动：

- `app/main.py`：注册 `funds` 路由。
- `frontend/src/components/Layout/SidebarMenu.vue`：在左侧主导航增加“基金分析”一级 Tab。
- `frontend/src/router/index.ts`：增加基金页面路由。

## 3. 核心类型

### 3.1. `FundSearchItem`

`FundSearchItem` 是基金搜索列表项，来自 `fund_name_em()` 并落库到 `fund_search_index`。

核心字段：

- `fund_code`：基金代码，例如 `012630`。
- `fund_name`：基金简称。
- `fund_type`：基金类型，例如指数型-股票、混合型、债券型。
- `pinyin_abbr`：拼音缩写。
- `pinyin_full`：拼音全称。
- `source`：数据来源，例如 `akshare`。
- `updated_at`：索引更新时间。

### 3.2. `FundBasicInfo`

`FundBasicInfo` 保存基金静态信息，落库到 `fund_basic_info`。

核心字段：

- `fund_code`：基金代码，例如 `000001`、`510300`。
- `fund_name`：基金名称。
- `fund_full_name`：基金全称。
- `fund_type`：股票型、混合型、债券型、货币型、QDII、ETF、LOF 等。
- `manager`：基金经理。
- `management_company`：基金公司。
- `custodian_bank`：托管银行。
- `inception_date`：成立日期。
- `asset_scale`：基金规模。
- `benchmark`：业绩比较基准。
- `investment_objective`：投资目标。
- `investment_strategy`：投资策略。
- `rating`：评级。
- `source`：数据来源，例如 `akshare`。
- `updated_at`：更新时间。

### 3.3. `FundNavRecord`

`FundNavRecord` 保存净值和收益率序列，落库到 `fund_nav_history`。

核心字段：

- `fund_code`
- `nav_date`
- `unit_nav`
- `accumulated_nav`
- `daily_return`
- `source`

### 3.4. `FundPerformanceItem`

`FundPerformanceItem` 保存阶段业绩，落库到 `fund_performance`。

核心字段：

- `fund_code`
- `performance_type`：年度业绩、阶段业绩。
- `period`：成立以来、今年以来、近1月、近3月、近6月、近1年、近3年等。
- `return_rate`
- `max_drawdown`
- `rank`
- `source`
- `updated_at`

### 3.5. `FundFeeInfo`

`FundFeeInfo` 保存交易状态和费用规则，落库到 `fund_fee_info`。

核心字段：

- `fund_code`
- `purchase_status`
- `redeem_status`
- `fixed_investment_status`
- `min_purchase_amount`
- `management_fee`
- `custody_fee`
- `sales_service_fee`
- `redeem_fee_rules`
- `source`
- `updated_at`

### 3.6. `FundDetailResponse`

`FundDetailResponse` 是前端详情页使用的聚合响应，不直接落库。

核心字段：

- `basic_info`
- `latest_nav`
- `nav_history`
- `performance`
- `fee_info`
- `data_warnings`
- `cache_status`

## 4. 核心功能

### 4.1. 基金搜索索引

目的：用户能快速通过基金代码、简称或拼音搜索基金。

实现方式：`FundDataService.search_funds()` 优先查询 MongoDB 的 `fund_search_index`。索引不存在或过期时，调用 `ChinaFundProvider.fetch_fund_list()` 拉取 `fund_name_em()`，标准化后批量 upsert。查询时对 `fund_code`、`fund_name`、`pinyin_abbr`、`pinyin_full` 做前缀或包含匹配，并限制返回数量。

调用链：

```text
frontend Funds/FundSearch.vue
  -> GET /api/funds/search?query=012630&limit=20
  -> app.routers.funds
  -> FundDataService.search_funds()
  -> fund_search_index
  -> ChinaFundProvider.fetch_fund_list() 仅在缓存缺失或过期时调用
```

稳定性要求：搜索接口不能因为单只基金详情接口失败而失败；列表索引拉取失败时，如果 MongoDB 有旧索引，则返回旧索引并带 `cache_status.stale=true`。

### 4.2. 基金详情聚合

目的：用户点进基金后能看到基础资料、最新净值、净值走势、阶段业绩和费用规则。

实现方式：`FundDataService.get_fund_detail(fund_code)` 优先读取 MongoDB。基础资料、净值、业绩和费用分别设置缓存时间，缓存缺失或过期时调用 provider 刷新对应数据。各类数据独立失败时写入 `data_warnings`，不阻断整个详情响应。

调用链：

```text
frontend Funds/FundDetail.vue
  -> GET /api/funds/{fund_code}
  -> FundDataService.get_fund_detail()
  -> fund_basic_info + fund_nav_history + fund_performance + fund_fee_info
  -> ChinaFundProvider 按需补齐缺失数据
```

标准化要求：provider 只向上层返回项目字段名，不向 `FundDataService` 暴露 AkShare 原始中文列名。`fund_fee_em(symbol, "申购费率（前端）")` 这类可能抛出 `KeyError` 的可选数据不影响交易状态、运作费用和赎回费展示。

### 4.3. 净值走势查询

目的：详情页可以按周期展示净值走势，避免每次都返回全部历史数据。

实现方式：后端提供 `GET /api/funds/{fund_code}/nav?period=1m|3m|6m|1y|all`。`FundDataService.get_nav_history()` 从 `fund_nav_history` 按日期过滤返回。缓存缺失时先拉取“成立来”数据并落库，再按周期裁剪。

调用链：

```text
frontend Funds/FundDetail.vue
  -> GET /api/funds/{fund_code}/nav?period=1y
  -> FundDataService.get_nav_history()
  -> fund_nav_history
```

### 4.4. API 路由

目的：前端基金页面通过独立 API 访问基金查询能力。

当前第一版路由：

- `GET /api/funds/search?query=&limit=`：搜索基金。
- `GET /api/funds/{fund_code}`：基金详情聚合。
- `GET /api/funds/{fund_code}/nav?period=`：净值走势。
- `POST /api/funds/{fund_code}/refresh`：手动刷新单只基金缓存。

响应形态沿用项目当前 API 约定：

```json
{
  "success": true,
  "data": {},
  "message": "..."
}
```

### 4.5. 前端基金入口

目的：用户可以从左侧导航直接进入基金查询，而不是在股票输入框里混用基金代码。

实现方式：在 `frontend/src/components/Layout/SidebarMenu.vue` 的“股票分析”菜单之后、“任务中心”之前增加一级菜单项：

```text
基金分析 -> /funds
```

`/funds` 默认重定向到 `/funds/search`。第一版页面只实现基金查询和详情展示：

- `/funds/search`：基金搜索和列表。
- `/funds/:code`：基金详情。

当前第一版点击左侧“基金分析”Tab 时进入 `/funds/search`。如果后端 `/api/funds/search` 尚未实现，页面显示“基金接口未接入”的空状态，不跳转到 404，也不复用股票分析页面。

前端交互要求：

- 搜索框输入做防抖，避免每个字符都请求后端。
- 连续搜索时取消或忽略旧请求结果，避免晚返回的旧结果覆盖新结果。
- 搜索结果为空、后端 404、后端 500、数据源失败分别显示不同提示。
- 详情页显示缓存更新时间和 `data_warnings`。

## 5. 实现步骤

### 5.1. 建立基金查询数据模型和索引契约【未开始】

目标：定义当前查询功能需要的模型和 MongoDB 集合，避免把基金分析字段提前混入查询阶段。

方案：新增 `app/models/fund.py`，定义 `FundSearchItem`、`FundBasicInfo`、`FundNavRecord`、`FundPerformanceItem`、`FundFeeInfo`、`FundDetailResponse`。MongoDB 使用 `fund_search_index`、`fund_basic_info`、`fund_nav_history`、`fund_performance`、`fund_fee_info`，并为 `fund_code`、`fund_name`、`pinyin_abbr`、`nav_date` 建索引。

产出/检查：能够导入 `app.models.fund`；集合索引可以初始化；字段名在服务、API 和前端类型中一致。

### 5.2. 接入 AkShare 基金查询 provider【未开始】

目标：把 AkShare 调用集中在 provider，保证业务服务不直接依赖原始中文列名和具体接口异常。

方案：新增 `tradingagents/dataflows/providers/china/fund.py`，实现 `fetch_fund_list()`、`fetch_basic_info(fund_code)`、`fetch_nav_history(fund_code)`、`fetch_performance(fund_code)`、`fetch_fee_info(fund_code)`。每个方法都返回标准化 dict/list，并把可恢复错误转换为 `data_warnings`。

产出/检查：给定 `012630` 和 `014767`，provider 至少能返回搜索项、基础资料、净值历史和可用费用信息；单个 AkShare 子接口失败不会导致 provider 整体崩溃。

### 5.3. 建立 `FundDataService` 缓存优先查询【未开始】

目标：实现稳定快速的基金查询服务，减少页面直接等待外部数据源的概率。

方案：新增 `app/services/fund_data_service.py`，实现：

- `search_funds(query, limit=20)`
- `get_fund_detail(fund_code)`
- `get_nav_history(fund_code, period="1y")`
- `refresh_fund(fund_code)`
- `refresh_search_index(force=False)`

服务默认缓存优先。搜索索引使用较长缓存时间；详情数据按基础资料、净值、业绩和费用分别判断是否过期。缓存过期但仍有旧数据时，优先返回旧数据并附带 `cache_status.stale=true`，手动刷新接口负责强制更新。

产出/检查：缓存命中时不调用 AkShare；缓存缺失时能拉取并写入 MongoDB；返回结构不包含 MongoDB `_id`；`012630` 和 `014767` 能通过同一套服务查询。

### 5.4. 增加基金查询 API 路由【未开始】

目标：前端可以通过独立后端接口访问基金查询能力。

方案：新增 `app/routers/funds.py` 并在 `app/main.py` 注册。路由包括搜索、详情、净值和手动刷新。所有路由沿用当前用户鉴权和统一响应格式。

产出/检查：登录后可调用 `GET /api/funds/search?query=012630`；当前本地该接口返回 `404`，实现完成后应返回 `012630` 的基金搜索项；查询不存在的基金返回空列表或清晰错误，不返回原始异常堆栈。

### 5.5. 增加前端基金查询页面和 API【未开始】

目标：用户可以从左侧“基金分析”入口完成基金搜索和详情查看。

方案：新增 `frontend/src/api/funds.ts`、`frontend/src/types/fund.ts`、`frontend/src/views/Funds/FundSearch.vue`、`frontend/src/views/Funds/FundDetail.vue`。在 `frontend/src/router/index.ts` 注册 `/funds`、`/funds/search`、`/funds/:code`，在 `SidebarMenu.vue` 增加“基金分析”一级 Tab。

产出/检查：用户点击左侧“基金分析”后进入 `/funds/search`；搜索 `012630` 和 `014767` 可以显示列表项；点击列表项进入详情页；接口未接入或失败时页面展示明确空状态，不进入 404。

### 5.6. 增加最小验证用例【未开始】

目标：确保基金查询稳定性和股票功能兼容。

方案：增加后端服务级测试或脚本，覆盖：

- `FundDataService.search_funds()` 能返回列表或空列表。
- `FundDataService.search_funds("012630")` 返回包含 `012630` 的列表。
- `FundDataService.search_funds("014767")` 返回包含 `014767` 的列表或明确空结果。
- `FundDataService.get_fund_detail("012630")` 返回基础资料、最新净值、阶段业绩和费用信息。
- `GET /api/funds/search?query=012630` 返回统一 API 响应。
- `POST /api/analysis/single` 股票请求仍保持原字段兼容。

前端至少执行 `npm run type-check`，后端至少执行基金服务的轻量脚本或相关 pytest。

产出/检查：测试通过；手工验证 `http://localhost:3000/` 可进入基金查询页面；`http://localhost:8000/api/health` 正常。

## 6. 当前进度和完成条件

当前进度：本文档已收敛为“稳定快速查询基金”的高优先级当前第一版实现方案，代码实现尚未开始，`5.1` 到 `5.6` 均为【未开始】。本地前端 `http://localhost:3000` 和后端 `http://localhost:8000/api/health` 已确认可访问；当前 `/api/funds/search?query=012630` 返回 `404`；AkShare 数据源已用 `012630` 完成基础资料、净值、阶段业绩、费用规则和可用持仓的前置验证。

当前第一版完成条件：

1. `5.1` 到 `5.6` 的 `产出/检查` 均已满足。
2. `012630` 和 `014767` 可以从前端搜索入口查询，并能打开基金详情页。
3. 缓存命中时基金搜索和详情不依赖 AkShare 实时可用。
4. 数据源局部失败时页面展示可用数据和明确提示，不进入空白页或 500。
5. 股票分析原有入口、任务中心和报告中心不发生回归。
6. 基金分析任务、买卖建议和报告生成不得阻塞本功能上线。
