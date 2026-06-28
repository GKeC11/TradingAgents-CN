---
name: module-usage-documentation
description: Create, review, and maintain module or plugin usage documentation. Use when Codex needs to write or update practical Markdown usage guides for project modules, plugins, framework integrations, reusable subsystems, SDK-style APIs, or convention documents that tell developers how to use something correctly.
---

# 模块使用文档

Use this skill for usage documentation: Markdown files whose main job is to tell developers how to correctly use a module, plugin, framework integration, reusable subsystem, SDK-style API, or project convention.

Do not use this skill for source-code analysis reports. Use `analysis-documentation` for documents explaining how an existing system works internally.

Do not use this skill for implementation plans. Use `implementation-plan-documentation` for documents defining what should be built next.

## Project-Specific References

- Read `references/project-initialization-guide.md` when writing or updating NoOutsiders project setup documentation, especially docs about using VS Code to iterate C++ and Puerts TypeScript.

## Workflow

1. Identify the documentation target: module, plugin, subsystem, API, framework integration, asset workflow, or project convention.
2. Identify the intended reader: gameplay programmer, tools programmer, designer, content author, build engineer, or future Codex agent.
3. Inspect existing docs and source-defined names before writing rules. Verify class names, module names, tag names, asset names, function names, and config paths locally.
4. Separate durable usage rules from current implementation state. Usage docs should teach correct usage; they should not become a progress report.
5. Define the ownership boundary first: what the module owns, what callers provide, what systems it must not replace, and what extension points are supported.
6. Document the minimum correct workflow before optional workflows.
7. Add anti-patterns for common misuse, especially where the project has already made a wrong turn.
8. After editing, scan headings and remove sections that describe current status, rollout progress, or one-off examples unless the user explicitly asked for them.

## Recommended Outline

For module or plugin usage documents, prefer this shape and trim sections that do not apply:

1. Purpose and scope: what the module is for, what problem it solves, and what it is not for.
2. Core principles: stable rules that should remain true across implementations.
3. Ownership and boundaries: which project layer owns state, lifecycle, authority, assets, and extension points.
4. Required setup: required plugins, module dependencies, config, base classes, components, interfaces, or assets.
5. Usage workflow: the minimum path to use the module correctly.
6. API and extension rules: public classes, interfaces, delegates, events, tasks, tags, data assets, config keys, and extension points.
7. Asset and data conventions: asset locations, naming, data split, default configuration, and editor workflow.
8. Network, lifecycle, and authority rules: initialization order, replication, prediction, cleanup, ownership, and server/client responsibilities.
9. Integration with related systems: input, animation, UI, AI, inventory, interaction, save/load, build, scripting, or external services.
10. Validation: compile checks, editor checks, runtime checks, data validation, packaged build checks, and minimal test assets.
11. Anti-patterns: forbidden usage, common mistakes, and what to do instead.
12. Examples: concise examples only when they clarify a general rule.

Use a shorter outline for small modules, but preserve the same order: purpose, principles, setup, usage workflow, extension rules, validation, anti-patterns.

## Usage Document Rules

- Write durable rules, not a snapshot of current adoption status.
- Do not add sections like "当前接入状态", "当前进度", "剩余事项", or "迁移步骤" unless the user explicitly asks for status tracking.
- Keep concrete current classes as examples, not as the main structure of the document.
- Put implementation examples under an "Examples" section and state that they are examples, not mandatory templates.
- Describe what callers should do and what the module guarantees.
- Describe what callers must not do when misuse would bypass lifecycle, authority, replication, or ownership rules.
- Prefer action-oriented wording such as "Use X for Y" and "Do not bypass Z".
- Prefer concise Chinese prose for Chinese project documentation.
- Keep Unreal, plugin, class, function, tag, file, module, and asset names in their original spelling and wrap them in backticks.

## Source Accuracy

- Verify source-defined names before documenting them.
- Preserve source casing exactly for classes, functions, tags, modules, plugins, config keys, and asset types.
- When a rule depends on an engine or plugin behavior, inspect the local source or existing project docs instead of relying on memory.
- If a behavior is inferred rather than source-confirmed, say so briefly or avoid stating it as a hard rule.

## Current-State Filtering

Usage documents should avoid project snapshots. Before finishing, remove or rewrite:

- Current progress summaries.
- Lists of currently modified files.
- "Already done" or "not yet done" sections.
- One-off migration notes.
- Narrow feature walkthroughs that only describe one current implementation.
- Specific class lists that are not needed to explain a general usage rule.

Keep current examples only when they help the reader apply a general rule:

```text
Use "For example, ..." under an Examples section.
Avoid making the example a top-level chapter.
Avoid turning example behavior into the generic module contract.
```

## Boundary Language

Good usage docs clearly separate responsibility:

- "The module owns..."
- "Callers provide..."
- "The asset config controls..."
- "The server is authoritative for..."
- "The UI only observes..."
- "The input layer only requests..."
- "The animation notify only signals..."
- "Do not put this responsibility in..."

Use this style when documenting framework integrations, gameplay systems, plugins, or reusable subsystems.

## Anti-Patterns

- Turning a usage guide into a source analysis document.
- Turning a usage guide into an implementation plan or migration checklist.
- Recording current接入状态 as a permanent rule.
- Making one feature's current implementation the generic rule for all future uses.
- Listing APIs without explaining when to use them and what they must not replace.
- Omitting lifecycle, authority, or ownership when the module affects gameplay state.
- Duplicating engine or plugin-provided concepts under project-specific names without a clear reason.

## Final Check

Before finishing a usage document:

1. Scan headings with `rg -n "^(#|##|###) " <file>`.
2. Confirm the document reads as "how to use this correctly", not "what we found" or "what we plan to build".
3. Confirm project status sections are absent unless explicitly requested.
4. Confirm exact source names are verified.
5. Confirm anti-patterns are specific enough to prevent misuse.
