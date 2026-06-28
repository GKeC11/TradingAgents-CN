---
name: temp-work-documentation
description: Write and revise temporary work-note Markdown documents for the current task, especially files under Docs/Temp. Use when Codex needs to record,整理, or update a short-lived requirement note, current implementation flow, task breakdown, or working agreement before or during implementation. Prefer concise implementation-flow chapters over full design-plan documentation.
---

# 临时工作文档

Use this skill for temporary Markdown documents whose purpose is to record the current task's requirements, decisions, and implementation flow. These documents are working notes, not long-term module design plans or plugin analysis reports.

## Intent

- Capture what the current work is trying to implement.
- Preserve user decisions and constraints from the conversation.
- Organize the next implementation steps so the work can continue without re-deriving context.
- Keep the document useful for the immediate task, not exhaustive for future readers.

## Location

- Prefer `Docs/Temp/` unless the user gives another path.
- Name the file close to the current requirement, using Chinese when the request is Chinese.
- Do not create broad permanent documentation unless the user asks for it.

## Chapter Shape

Default to implementation-step chapters. For task-flow notes, each top-level `##` section should be one concrete implementation step, ordered in the sequence the work should be done.

Preferred shape:

```text
## 1. 配置或准备某项输入
## 2. 修改某个系统或文件
## 3. 实现某个运行时流程
## 4. 接入某个 UI / 输入 / 配置
## 5. 验证完整流程
```

Do not add extra framework chapters such as `需求目标`, `当前约束`, `配置或数据结构`, `待确认事项`, or `暂不处理` when the user asks for a step-by-step temporary implementation document. Put constraints, file paths, data structures, and pending notes inside the relevant implementation step instead.

Only use meta chapters like `需求目标` or `当前约束` when the user explicitly asks for a requirement summary, decision record, or broader planning note instead of an implementation-step document.

## Ownership Markers

When the user asks to show which steps are done by AI versus the developer, mark ownership directly in each step heading instead of adding a separate ownership chapter.

Preferred heading format:

```text
## 1. Configure or prepare inputs（开发者，已完成）
## 2. Modify a system or file（AI，已实现）
## 3. Verify the complete flow（开发者，待验证）
```

Use concise owners such as `AI`, `开发者`, or `共同`, and concise statuses such as `已完成`, `已实现`, `待实现`, `待验证`, or `部分已实现`.

## Writing Rules

- Keep the document concise and operational.
- Prefer bullet lists, small tables, and ordered steps.
- Avoid long background explanations, plugin tutorials, or broad architecture essays.
- Do not over-specify code before implementation details are confirmed.
- Record user corrections as constraints. Example: "具体道具通过 Excel 配置，不为每个道具新增 Native GameplayTag。"
- Separate confirmed decisions from pending assumptions.
- Use concrete file paths when they are known.

## Difference From Implementation Plans

Use `implementation-plan-documentation` for durable feature/module implementation plans with ownership, dependencies, architecture, acceptance criteria, and future extension points.

Use this skill when the document is temporary and mainly exists to organize the current turn or near-term work.
