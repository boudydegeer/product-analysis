---
name: context-save
description: Save context notes or documents for an FCToolsHub module. Usage: /context-save <module> "note" or /context-save <module> --doc "name"
---

# Context Save - FCToolsHub

Save important information that Claude should remember in future sessions.

## Usage

### Mode 1: Simple note (default)

```
/context-save <module> "Your note here"
```

Adds a line to the "Context notes" section of the module's CLAUDE.md.

**Example:**
```
/context-save api "The TransformsCamelCaseInput trait must be used in all FormRequests"
```

Result in `apps/api/CLAUDE.md`:
```markdown
## Context notes

- The TransformsCamelCaseInput trait must be used in all FormRequests (2026-01-06)
```

### Mode 2: Complete document

```
/context-save <module> --doc "document-name"
```

Creates a document in `apps/<module>/docs/context/<name>.md` and adds a reference in CLAUDE.md.

**Example:**
```
/context-save api --doc "auth-flow"
```

Result:
1. Creates `apps/api/docs/context/auth-flow.md`
2. Adds to CLAUDE.md:
```markdown
## Context documents

- `docs/context/auth-flow.md` - [description]
```

---

## Available Modules

| Module | CLAUDE.md | docs/context/ Folder |
|--------|-----------|---------------------|
| `api` | `apps/api/CLAUDE.md` | `apps/api/docs/context/` |
| `mobile` | `apps/mobile/CLAUDE.md` | `apps/mobile/docs/context/` |
| `app` | `apps/app/CLAUDE.md` | `apps/app/docs/context/` |
| `admin` | `apps/admin/CLAUDE.md` | `apps/admin/docs/context/` |
| `web` | `apps/web/CLAUDE.md` | `apps/web/docs/context/` |
| `contracts` | `packages/contracts/docs/CLAUDE.md` | `packages/contracts/docs/context/` |

---

## What to Save

**Simple notes (mode 1):**
- Location of important files
- Module-specific conventions
- Gotchas and things to avoid
- Quick decisions

**Documents (mode 2):**
- Complex flows (auth, checkout, etc.)
- Feature architecture
- Detailed implementation guides
- Important historical context

---

## Implementation

When this skill is invoked, Claude should:

1. Identify the module and its CLAUDE.md
2. If simple note:
   - Look for "## Context notes" section (create if it doesn't exist)
   - Add the note with date
   - Make commit
3. If document:
   - Create `docs/context/` folder if it doesn't exist
   - Create the .md file
   - Ask the user for content
   - Add reference in CLAUDE.md
   - Make commit
