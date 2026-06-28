# TradingAgents 使用文档

本文档说明如何从本地源码环境启动 TradingAgents-CN，并完成初始化、登录和基本验证。

## 适用范围

本文档适用于当前仓库的前后端分离源码启动方式：

- 后端：FastAPI，入口为 `python -m app`，默认端口 `8000`
- 前端：Vue 3 + Vite，目录为 `frontend/`，默认端口 `3000`
- 数据库：MongoDB，默认端口 `27017`
- 缓存：Redis，默认端口 `6379`

## 前置条件

启动前确认以下环境可用：

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- MongoDB
- Redis
- 已安装前端依赖 `frontend/node_modules`
- 已安装后端依赖的虚拟环境，例如 `.venv-run`

当前仓库中常用的后端 Python 解释器路径为：

```powershell
.\.venv-run\Scripts\python.exe
```

## 1. 启动依赖服务

后端启动时会初始化 MongoDB 和 Redis。如果这两个服务不可用，后端会启动失败。

如果使用 Docker Desktop 提供 MongoDB 和 Redis，先启动 Docker Desktop，并确认端口已经监听：

```powershell
netstat -ano | Select-String ':27017|:6379'
```

看到 `27017` 和 `6379` 处于 `LISTENING` 后，再启动后端。

## 2. 初始化配置和默认账号

首次使用或登录提示用户不存在时，需要导入基础配置并创建默认管理员。

在仓库根目录执行：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
.\.venv-run\Scripts\python.exe scripts\import_config_and_create_user.py --host --mongodb-host localhost --mongodb-port 27017
```

脚本会默认读取 `install/database_export_config_*.json` 中最新的配置文件，导入以下基础数据：

- 系统配置
- LLM 提供商配置
- 模型目录
- 平台配置
- 数据源分组
- 市场分类
- 默认用户和示例标签数据

初始化成功后，默认登录信息为：

```text
用户名：admin
密码：admin123
```

## 3. 启动后端服务

当前 `.env` 可能包含 Docker 环境配置，例如 `DOCKER_CONTAINER=true`、`MONGODB_HOST=mongodb`。源码本地启动时建议在命令中覆盖为本机地址。

在仓库根目录执行：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$env:DEBUG='false'
$env:DOCKER_CONTAINER='false'
$env:TRADINGAGENTS_LOG_DIR='logs'
$env:MONGODB_HOST='localhost'
$env:MONGODB_PORT='27017'
$env:MONGODB_USERNAME='admin'
$env:MONGODB_PASSWORD='tradingagents123'
$env:MONGODB_AUTH_SOURCE='admin'
$env:MONGODB_DATABASE='tradingagentscn'
$env:REDIS_HOST='localhost'
$env:REDIS_PORT='6379'
$env:REDIS_PASSWORD='tradingagents123'
.\.venv-run\Scripts\python.exe -m app
```

看到类似以下日志表示后端启动成功：

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

验证后端：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/api/health'
```

正常响应会包含：

```json
{"status":"ok","service":"TradingAgents-CN API"}
```

## 4. 启动前端网页

在仓库根目录执行：

```powershell
cd frontend
npm run dev
```

看到类似以下日志表示前端启动成功：

```text
VITE ready
Local: http://localhost:3000/
```

打开网页：

```text
http://localhost:3000/
```

如果浏览器没有自动打开，手动访问该地址即可。

## 5. 登录验证

访问 `http://localhost:3000/` 后使用默认账号登录：

```text
用户名：admin
密码：admin123
```

如果登录失败：

1. 确认已执行初始化脚本。
2. 确认后端已在初始化之后重启。
3. 确认后端连接的数据库是 `tradingagentscn`。
4. 查看后端日志中是否仍提示 `用户不存在`。

## 6. 常用检查命令

检查端口监听：

```powershell
netstat -ano | Select-String ':3000|:8000|:27017|:6379'
```

检查前端：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:3000'
```

检查后端：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/api/health'
```

## 7. 常见问题

### 后端提示 `DEBUG` 解析失败

如果报错类似：

```text
Input should be a valid boolean, input_value='release'
```

说明当前 PowerShell 会话里存在 `DEBUG=release`。启动后端前显式覆盖：

```powershell
$env:DEBUG='false'
```

### 后端连接 `mongodb:27017` 失败

源码本地启动时不能使用 Docker 内部主机名 `mongodb`。启动后端或初始化脚本时使用：

```powershell
--mongodb-host localhost --mongodb-port 27017
```

后端启动命令中也需要覆盖：

```powershell
$env:MONGODB_HOST='localhost'
```

### 初始化脚本出现 GBK 编码错误

Windows 控制台可能无法输出 emoji，导致 `UnicodeEncodeError`。执行脚本前设置：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
```

### 前端启动后浏览器没有自动打开

这是正常现象。手动访问：

```text
http://localhost:3000/
```

### 前端启动时出现 Sass deprecation 警告

类似 `legacy JS API is deprecated` 的 Sass 警告不影响页面访问。

### 登录仍提示账号密码错误

先执行初始化脚本，再重启后端。后端启动时会建立数据库连接，旧进程可能还没读到新导入的用户。

## 8. 推荐启动顺序

每次从零启动时按以下顺序操作：

1. 启动 MongoDB 和 Redis。
2. 首次使用时执行初始化脚本。
3. 启动或重启后端 `python -m app`。
4. 启动前端 `npm run dev`。
5. 打开 `http://localhost:3000/`。
6. 使用 `admin/admin123` 登录。

