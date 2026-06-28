# NoOutsiders 项目初始化指南

这份指南用于说明如何用 VS Code 迭代 `NoOutsiders` 项目。它关注开发入口和最小正确配置：启动 Unreal Editor、附加 C++/TypeScript 调试、持续编译 Puerts TypeScript，以及理解项目内基础脚本分层。

## 适用范围

- C++ 迭代：用 VS Code 启动 `UnrealEditor.exe`；需要断点时再手动附加 C++ 调试器，并使用 Unreal 的 natvis 调试视图。
- TypeScript 迭代：用 `tspc` 编译 `TypeScript/**/*` 到 `Content/JavaScript`，并通过 Puerts debug port 附加调试。
- 项目脚本分层：`TypeScript/Framework` 放通用 Puerts/工具基础设施，`TypeScript/GameFramework` 放项目级游戏入口和游戏侧库。

不要把项目初始化文档写成个人机器状态记录。路径、扩展、端口和脚本应该作为可复用约定说明；本地安装位置不同的内容只作为需要替换的占位说明。

## VS Code 必要文件

项目工作区至少应保留以下配置：

- `.vscode/launch.json`：启动/附加 Unreal Editor，以及附加 Puerts TypeScript 调试。
- `.vscode/tasks.json`：运行 `tspc --watch` 持续编译 TS。
- `.vscode/settings.json`：让 VS Code 使用项目内的 TypeScript SDK。
- `.vscode/c_cpp_properties.json`：使用 Unreal 生成的 compile commands 驱动 C++ IntelliSense。

`settings.json` 应保持：

```json
{
    "typescript.tsdk": "node_modules/typescript/lib",
    "typescript.enablePromptUseWorkspaceTsdk": true
}
```

这样 VS Code 诊断会使用项目锁定的 `typescript` 版本，而不是编辑器自带的新版本。

## 推荐 VS Code 扩展

项目推荐在 `.vscode/extensions.json` 中声明核心扩展：

```json
{
    "recommendations": [
        "ms-vscode.cpptools",
        "redhat.vscode-yaml"
    ]
}
```

扩展用途：

- `ms-vscode.cpptools`：提供 C++ IntelliSense 和 Windows 下 `cppvsdbg` 调试类型。
- `redhat.vscode-yaml`：维护 Codex skill、CI 或工具配置时提供 YAML 语法支持。

Node/JavaScript 调试器、TypeScript 语言服务、Markdown 预览由 VS Code 内置能力提供；`launch.json` 中的 `type: "node"` 不需要额外安装扩展。

如果项目后续加入 `.editorconfig` 或 ESLint 配置，再把 `EditorConfig.EditorConfig` 或 `dbaeumer.vscode-eslint` 加入推荐列表。

## launch.json 配置

项目需要三个常用启动/调试配置：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Unreal Editor",
            "type": "cppvsdbg",
            "request": "launch",
            "noDebug": true,
            "program": "D:/UGit/UnrealEngine/Engine/Binaries/Win64/UnrealEditor.exe",
            "args": [
                "D:/UGit/NoOutsiders/NoOutsiders.uproject"
            ],
            "cwd": "D:/UGit/UnrealEngine/Engine/Binaries/Win64",
            "console": "integratedTerminal"
        },
        {
            "name": "Attach Unreal Editor C++",
            "type": "cppvsdbg",
            "request": "attach",
            "processName": "UnrealEditor.exe",
            "visualizerFile": "D:/UGit/UnrealEngine/Engine/Extras/VisualStudioDebugging/Unreal.natvis"
        },
        {
            "name": "Attach Unreal Editor TS",
            "type": "node",
            "request": "attach",
            "address": "127.0.0.1",
            "port": 8080,
            "cwd": "${workspaceFolder}",
            "sourceMaps": true,
            "skipFiles": [
                "<node_internals>/**"
            ],
            "outFiles": [
                "${workspaceFolder}/Content/JavaScript/**/*.js"
            ],
            "resolveSourceMapLocations": [
                "${workspaceFolder}/Content/JavaScript/**/*.js",
                "!**/node_modules/**"
            ]
        }
    ]
}
```

使用规则：

- `program`、`cwd`、`visualizerFile` 指向本机 Unreal Engine 安装目录，换机器时只改这些路径。
- `args` 第一个值指向当前 `.uproject`。
- `Launch Unreal Editor` 用于从 VS Code 启动编辑器，不保持 VS Code 对 Unreal Editor 的调试连接。
- `Attach Unreal Editor C++` 用于编辑器已经启动后附加到 `UnrealEditor.exe`。
- `Attach Unreal Editor TS` 用于附加 Puerts TypeScript 调试，默认端口为 `8080`。

Puerts 调试端口来自 `Config/DefaultPuerts.ini`：

```ini
[/Script/Puerts.PuertsSetting]
AutoModeEnable=True
DebugEnable=True
DebugPort=8080
WaitDebugger=False
```

多进程调试时，Puerts 会基于默认端口偏移：Editor 常用 `8080`，Dedicated Server 常用 `9079`，Client 进程常用 `8090`、`8100`、`8110`。

## TypeScript 初始化和迭代

首次配置或 TS 层需要修复时，执行：

```powershell
node Plugins/Puerts/enable_puerts_module.js
npm install
```

日常编译：

```powershell
npm run build
```

持续监听：

```powershell
npm run watch
```

当前 `package.json` 的基础脚本应保持：

```json
{
    "scripts": {
        "build": "npx tspc -p tsconfig.json",
        "watch": "npx tspc --watch -p tsconfig.json"
    }
}
```

不要用 `tsc` 替代 `tspc`。项目依赖 `ts-patch` 和 `typescript-transform-paths`，编译输出目录是 `Content/JavaScript`。

关键 `tsconfig.json` 约定：

- `module` 使用 `commonjs`。
- `moduleResolution` 使用 `node`。
- `sourceMap` 必须为 `true`，否则 VS Code 无法把断点稳定映射回 TS 源码。
- `paths` 中 `@root/*` 指向 `TypeScript/*`。
- `include` 只覆盖 `TypeScript/**/*`。

业务代码导入统一使用小写 `@root`：

```ts
import { PuertsUtil } from "@root/Framework/Util/PuertsUtil";
```

不要把常规 import 写成 `@Root`。`@Root` 只可能出现在 Mixin 动态加载路径等运行时约定中，不能和 `tsconfig.json` 的 `@root/*` 混用。

## TypeScript/Framework 基础脚本

`TypeScript/Framework` 放项目无关或尽量通用的 Puerts 基础设施。

当前基础目录：

- `TypeScript/Framework/Console/ConsoleCommandRegister.ts`
  - 把 TS 函数包装成 Puerts delegate。
  - 通过 `UE.DMPuertsLibrary.RegisterConsoleCommand` 注册 Unreal 控制台命令。
- `TypeScript/Framework/Mixin/MixinDefine.ts`
  - 维护需要运行时加载的 Mixin 脚本路径。
  - 新增 Blueprint Mixin 后要在这里注册路径。
- `TypeScript/Framework/Util/LogUtil.ts`
  - 统一 TS 日志输出和上下文标签。
- `TypeScript/Framework/Util/NetworkUtil.ts`
  - 放通用网络请求/协议辅助逻辑。
- `TypeScript/Framework/Util/PuertsUtil.ts`
  - 封装 Blueprint class 加载、Mixin 注册、UE/JS 数组转换、脚本加载等 Puerts 基础能力。

使用原则：

- 新增通用 Puerts 能力优先放在 `Framework/Util` 或 `Framework/Console`。
- 不要把具体玩法、UI 页面流程、房间/对局业务状态写进 `Framework`。
- Blueprint Mixin 应优先使用 `PuertsUtil.LoadClass(...)` 和 `PuertsUtil.Mixin(...)`，避免在业务脚本里重复直接调用底层加载 API。

## TypeScript/GameFramework 基础脚本

`TypeScript/GameFramework` 放项目级游戏入口和游戏侧通用库，允许依赖 `NoOutsiders` 的 GameInstance、Gameplay Message、控制台命令等项目约定。

当前基础目录：

- `TypeScript/GameFramework/Core/TS_GameInstance.ts`
  - 继承 `UE.NOGameInstance`。
  - 覆盖 `TS_Init()`，作为 C++ `UDMGameInstance::OnStart()` 调用到 TS 的入口。
  - 启动时注册控制台命令，加载 Mixin 配置，完成后调用 `NotifyScriptInitialized()`。
- `TypeScript/GameFramework/Library/ConsoleCommandLibrary.ts`
  - 声明项目常用 TS 控制台命令。
  - 当前包括 `CMD_MixinFromConfig` 和 `CMD_LogAllMixinClassesAndMethods`。
- `TypeScript/GameFramework/Library/GameplayMessageLibrary.ts`
  - 封装项目对 Gameplay Message 的 TS 使用方式。

启动链路：

1. `Config/DefaultEngine.ini` 指向 `/Game/Blueprints/TypeScript/GameFramework/Core/TS_GameInstance.TS_GameInstance_C`。
2. 该 Blueprint 继承项目 C++ `UNOGameInstance`。
3. `UNOGameInstance` 继承 `UDMGameInstance`。
4. `UDMGameInstance::OnStart()` 调用 Blueprint/Puerts 暴露的 `TS_Init()`。
5. `TS_GameInstance.ts` 在 `TS_Init()` 中注册 TS 层基础能力并通知脚本层初始化完成。

使用原则：

- 项目启动、全局命令、项目级消息工具可以放在 `GameFramework`。
- 具体 UI 页面逻辑放在 `TypeScript/UI`。
- 可被多个玩法或 UI 复用、但不依赖项目启动链路的工具，优先放在 `TypeScript/Library` 或 `TypeScript/Framework`。

## 推荐迭代流程

1. 启动 `npm run watch` 或 VS Code task `ts-patch watch - project`。
2. 用 `Launch Unreal Editor` 启动编辑器；需要 C++ 断点时再用 `Attach Unreal Editor C++` 附加。
3. 确认 `Config/DefaultPuerts.ini` 中 `DebugEnable=True` 且 `DebugPort=8080`。
4. 需要调 TS 时，使用 `Attach Unreal Editor TS`。
5. 修改 TS 后等待 watch 输出到 `Content/JavaScript`，再在编辑器中触发相关流程。
6. 修改 C++ 后按 Unreal 项目的正常编译/热重载规则处理；涉及反射、类层级、构造逻辑时优先重启编辑器验证。

## 常见错误

- 没有运行 `npm install`，导致 `npx tspc`、`ts-patch` 或 `typescript-transform-paths` 不存在。
- VS Code 没有使用 `node_modules/typescript/lib`，导致编辑器诊断和 `npm run build` 结果不一致。
- `sourceMap` 被关闭，导致 TS 断点无法命中或映射到错误文件。
- `launch.json` 的 `outFiles` 没有指向 `Content/JavaScript/**/*.js`。
- 常规 TS import 写成 `@Root/...`，导致模块解析失败。
- 新增 Mixin 文件后没有在 `TypeScript/Framework/Mixin/MixinDefine.ts` 注册。
- 编辑器、多客户端、Dedicated Server 同时调试时仍使用同一个 TS debug port。
