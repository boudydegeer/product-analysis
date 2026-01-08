# .claude Directory

This directory contains project-specific Claude Code configuration.

## Structure

```
.claude/
├── README.md           # This file
├── context/            # Project context files
└── skills/             # Custom Claude Code skills
    ├── README.md       # Skills documentation
    ├── update-plan-status/
    │   └── skill.yaml  # Auto-update plan status
    └── sync-plan-status/
        └── skill.yaml  # Intelligent status sync
```

## What is this?

Claude Code supports project-specific skills that automate workflows and enforce quality standards. These skills are:

- **Versioned in git** - All team members get the same automation
- **Project-specific** - Tailored to this project's workflow
- **Automatically detected** - Claude Code loads them on startup

## Skills in This Project

See `skills/README.md` for detailed documentation on available skills.

## Global vs Project Skills

- **Global skills** (`~/.claude/skills/`): User-wide, not versioned
- **Project skills** (`.claude/skills/`): Project-specific, versioned in git

Project skills take precedence when names conflict.

## Context Directory

The `context/` directory contains project-specific context files that help Claude understand the codebase structure and conventions. These files are loaded automatically when working in this project.
