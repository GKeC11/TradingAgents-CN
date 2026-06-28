# Project Codex Environment

This directory stores project-local Codex configuration notes for TradingAgents-CN.

## Project Skills

Codex discovers repository skills from `.agents/skills/`, not from `.codex/skills/`.
Do not keep a second copy under `.codex/skills/`, because VS Code Codex may show duplicate `$` skill entries when both paths exist.

Each skill directory under `.agents/skills/` contains:

- `SKILL.md`: the instruction file Codex reads before using the skill.
- `agents/openai.yaml`: optional UI metadata and default prompt.
- `references/`: optional supporting documents used by the skill.

## Current Skill Set

- `analysis-documentation`
- `design-thinking-partner`
- `generate-commit-comment`
- `implementation-plan-documentation`
- `module-usage-documentation`
- `temp-work-documentation`

## Usage

Mention a skill by name when you want Codex to use it, for example:

```text
Use design-thinking-partner to review the fund-analysis architecture.
```

When a task clearly matches a skill, Codex should read that skill's `SKILL.md` from `.agents/skills/` before acting.
