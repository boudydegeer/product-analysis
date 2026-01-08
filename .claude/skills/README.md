# Project Skills

This directory contains custom Claude Code skills specific to the Product Analysis Platform project.

## Available Skills

### update-plan-status
**Type**: Auto-invocable (used automatically by Claude)
**Purpose**: Updates plan status in `docs/plans/index.md` automatically during workflow stages

**Triggers**:
- After `/brainstorming` → Registers plan as Backlog
- After `/writing-plans` → Updates to Ready
- When first todo marked `in_progress` → Updates to In Progress
- When all todos completed → Updates to Done
- When blocked → Updates to Blocked

### sync-plan-status
**Type**: User-invocable
**Purpose**: Intelligently analyzes codebase and synchronizes plan statuses

**Usage**: `/sync-plan-status`

**What it does**:
- Runs verification script
- Analyzes implementation state (files, commits, tests)
- Suggests status updates with evidence
- Asks for confirmation before updating

## How Skills Work

Claude Code automatically detects skills in `.claude/skills/` directories at both:
- **Global level**: `~/.claude/skills/` (user-wide skills)
- **Project level**: `<project>/.claude/skills/` (project-specific skills)

Project-level skills take precedence over global skills with the same name.

## Versioning

These skills are versioned in git so all team members have access to the same workflow automation.
