---
name: implementation-plan-documentation
description: Create, review, restructure, and maintain implementation-plan Markdown documents. Use when Codex writes or edits module implementation plans, feature design plans, phased rollout plans, dependency plans, integration plans, acceptance criteria, or project-specific build steps for work that has not yet been fully implemented.
---

# 实现方案文档

Use this skill for implementation-plan documentation: Markdown files whose main job is to define the smallest concrete implementation that should be built now: what it builds, where it belongs, what current dependencies it needs, how to implement it, and what concrete output counts as done.

Do not use this skill for pure analysis of an existing plugin, engine subsystem, or source-code behavior. Use the analysis-documentation skill for that.

## Workflow

1. Identify the implementation target: module, feature, class, asset type, integration path, or migration.
2. Define only the current minimal scope. Mention non-goals only when they prevent likely over-implementation.
3. Define ownership and boundaries before listing steps. Make clear which plugin, project module, asset, or subsystem owns each responsibility.
4. List only dependencies required by the current implementation. Do not list conditional or future dependencies unless the user explicitly asks.
5. Explain the core types and core features before the implementation steps. Readers should understand the key classes and runtime/editor call chains before seeing execution phases.
6. Write implementation steps as executable phases, not a raw file-by-file TODO list. Each step should state the implementation goal, the chosen implementation approach, and the concrete output or check that proves the step is complete.
7. Finish with current progress, remaining current-scope work, and completion criteria. Avoid broad deferred-work lists.
8. When updating an existing plan after implementation work, mark each implementation step's current status and distinguish code that has landed from work that has been compiled, run, or asset-validated.
9. After editing, scan headings and ensure the document reads as a plan, not a source analysis dump.

## Minimal Plan Rules

- Default to the smallest plan that implements the requested function.
- Do not document future features, future architecture, possible extensions, optional polish, or speculative integrations.
- Do not add sections just because the outline has them. If a section does not directly help implement the current function, omit it.
- If future work must be mentioned to prevent scope confusion, keep it to one short `不做：...` list.
- Do not add a standalone `当前第一版不做` chapter or broad non-goal list. Put only necessary exclusions into the goal/scope paragraph, ownership boundary, dependency notes, or the exact implementation step they affect.
- Omit broad exclusions that are already implied by current scope or delegated elsewhere, such as `编辑器模块不内置图片识别`, `不生成最终美术模型`, `不做 Mask/PCG`, or `不生成运行时 UI`, unless they directly change a current implementation dependency, file layout, API contract, or acceptance check.
- Do not keep generic boundary boilerplate such as `第一版边界：...`, `不做：...`, or `不负责：...` just to make the document feel complete; include a boundary only when it directly changes a current implementation step, dependency, API contract, or ownership decision.
- Do not add `使用规范`, `完成标准`, `Usage rules`, or `Completion criteria` sections when they only restate implementation steps, current-scope behavior, or obvious acceptance checks. Keep those details inside the relevant implementation step instead.
- Prefer concrete current-scope sentences over broad system descriptions.
- Keep code skeletons minimal and include them only when they clarify a contract that must be implemented now.
- A good plan should let a developer implement the current feature without suggesting unrelated follow-up work.

## Recommended Outline

For module or feature implementation plans, prefer this shape and trim sections that do not apply:

1. Goal and first-version scope: what the plan builds now, current behavior, and only necessary non-goals.
2. Module ownership, dependencies, and code structure: code location, plugin enablement, Build.cs modules, target directories, files, and ownership boundaries needed now.
3. Core types: key classes, inheritance, data ownership, lifecycle, responsibility split, and non-responsibilities.
4. Core features: group feature capabilities by purpose. For each feature, describe its goal, implementation approach, and runtime/editor call chain.
5. Implementation steps: ordered executable phases.
6. Optional usage rules: only asset workflow, configuration workflow, naming rules, designer/developer guidance, or project conventions that are not already stated in the implementation steps.
7. Optional current progress, remaining items, and completion criteria: only when the plan tracks real status or has non-obvious acceptance conditions not already covered by the steps.

For small project modules whose first version is narrow, prefer this compact chapter order:

1. Goal, principles, and first-version scope
2. Module ownership, dependencies, and code structure
3. Core types
4. Core features
5. Implementation steps
6. Optional current progress and remaining items, only when status tracking is needed

For very small features, collapse the document further:

1. 目标和范围
2. 依赖和归属
3. 核心类型
4. 实现步骤
5. 当前进度和剩余事项（仅在需要跟踪状态时保留）

## Section Ordering Rules

- Number implementation-plan headings by hierarchy. Top-level chapters should use `1.`, `2.`, `3.` prefixes, and child chapters should use `3.1.`, `3.2.`, `4.1.` prefixes. Example: `## 1. 目标、原则和当前第一版范围`, `## 3. 核心类型`, `### 3.1. FSceneGeneratePlan`.
- Keep closely related plan context together. Put scope and non-goals under the goal/principles chapter instead of making a separate top-level chapter unless the scope is unusually large.
- Put file layout under module ownership/dependencies instead of making a separate top-level chapter unless the document is mainly about repository migration or package layout.
- When showing a target file layout with multiple files, use a readable directory tree instead of a flat list of full paths, so ownership and grouping are visible at a glance.
- Name the class-focused chapter `核心类型` when it primarily describes classes, structs, factories, assets, or editor toolkits. Use `核心设计` only when it covers broader architecture beyond types.
- Name the feature chapter `核心功能`, not `功能实现方案`.
- Under `核心功能`, write by feature capability instead of by file or class. Each feature should explain: purpose, implementation approach, and call chain.
- Examples of `核心功能` topics include config resolution, runtime projection, widget display, asset generation, validation, write flow, editor flow, and error handling.
- Keep low-level data format details, parsing rules, and error handling inside the relevant core feature instead of making isolated subsections disconnected from user-visible behavior.
- Put core types and core features before implementation steps. A reader should know what is being built and how it runs before reading execution phases.
- Do not put code skeletons only in the implementation steps when the same type also has a core-design section. Keep the main explanation in core types or core features; implementation steps can reference paths and contracts only when needed.
- Do not keep both `最小实现` and `实现步骤` when they describe the same execution flow. If the content is procedural, keep it under `实现步骤`; if it is architectural behavior, keep it under `核心功能`; do not duplicate it in both places.
- Put usage rules, asset conventions, naming guidance, and designer workflow after implementation steps only when they add information not already present in the steps.
- End with current progress, remaining items, or completion criteria only when the document needs real status tracking or non-obvious acceptance conditions. Keep status and scope-control information out of the middle of the plan.
- If a document has both code structure and implementation steps, code structure should describe the target file layout; steps should describe goal-oriented execution phases.
- Do not add a standalone validation chapter. If a check guides implementation, put it in the relevant implementation step; if it defines done, put it in completion criteria.
- Do not add a standalone future-extension chapter. Avoid `明确延期` unless the user explicitly asked to track deferred work or a specific non-goal prevents over-implementation.

## Dependency Rules

- List required-now dependencies only. Do not add every plausible module to the current dependency list.
- Tie each dependency to a concrete code reference or planned feature.
- Do not mention UI, interaction, equipment, editor, or gameplay modules unless the current implementation directly includes their headers or types.
- State when a plugin must be enabled in `.uproject` or `.uplugin` separately from when a module must be added to `.Build.cs`.
- If a dependency is intentionally excluded, mention it only when it is a likely mistake someone would otherwise add.

## Implementation Step Rules

- Steps should be ordered so a developer can execute them without guessing prerequisites.
- When progress is being tracked, put the status at the end of each implementation-step heading, using full-width brackets. Use the document heading numbering before the step title. Examples: `### 5.2. 建立 DialogueConfig 配置【已完成】`, `### 5.3. 建立 DialogueContext 和 Library 入口【未开始】`, `### 5.4. 建立 DialogueSubsystem【已实现，未验证】`. Do not add a separate `状态：...` line.
- Do not mark a step as fully complete unless its `产出/检查` has also been satisfied. If code exists but compile/runtime/asset validation was not run, mark it as `已实现，未验证` or `部分完成`.
- Each step should describe a meaningful implementation goal and its implementation plan. Prefer the shape: `目标：...；方案：...；产出/检查：...`.
- Do not write implementation steps as a mechanical list of every file to create, every class to declare, or every field to add. Put target file layout under module ownership/code structure, and put class responsibilities under core types.
- A step may reference concrete paths and exact class names when they clarify ownership or execution, but the step should still explain why that work exists and how it should be implemented.
- Group related file edits into one coherent phase, such as module registration, data configuration, runtime projection, widget display, asset setup, or validation.
- Include minimal code skeletons only when they clarify the implementation contract.
- Do not include broad tutorials for engine systems unless the plan depends on a specific project convention.
- Keep non-goals near the relevant step when they prevent common over-implementation.
- Avoid steps like `Create A.h`, `Create A.cpp`, `Create B.h` unless the document is a migration checklist. Replace them with goal-oriented steps such as `建立运行时模块边界`, `定义地图配置契约`, or `串联 Widget 显示流程`.

## Writing Rules

- Prefer concise Chinese prose for Chinese project documentation.
- Keep Unreal, plugin, class, function, tag, file, and module names in their original spelling and wrap them in backticks.
- Use `当前第一版` wording to control scope. Avoid `后续再接入` unless the user asks for staged planning.
- Avoid vague promises such as `完善系统`. Use verifiable outputs such as `创建 DataTable 并能在 Widget 中显示底图`.
- Preserve source-defined names and casing. Verify uncertain symbols in local source before documenting them.

## Anti-Patterns

- Turning an implementation plan into a plugin analysis document.
- Adding project-owned managers before the ownership boundary requires one.
- Reimplementing plugin-provided runtime systems in a project plan without a documented reason.
- Mixing future UI, interaction, inventory, equipment, and editor tooling into the first-version checklist.
- Keeping a `当前第一版不做` list with generic exclusions that do not affect current implementation, such as final art, runtime UI, Mask/PCG, or external AI boundaries already covered by scope.
- Adding future features or possible extensions when the user asked for a minimal implementation plan.
- Listing dependencies without explaining what code or feature needs them.
- Splitting deferred scope into a separate extension chapter when it duplicates the remaining-items chapter.
- Using `功能实现方案` as a chapter name when the intended content is feature purpose, implementation approach, and call chain; use `核心功能` instead.
