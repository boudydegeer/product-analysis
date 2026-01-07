---
name: context-load
description: Load FCToolsHub context by module, feature or migration. Usage: /context-load <target>
---

# Context Loader - FCToolsHub

Load the relevant context to work on a specific part of the project.

## Usage

```
/context-load <target>
```

## Available Targets

### Modules (load complete module context)

| Target | Description | Main Files |
|--------|-------------|-----------|
| `api` | Laravel Backend | `apps/api/CLAUDE.md`, `packages/contracts/docs/CLAUDE.md` |
| `mobile` | Flutter app | `apps/mobile/CLAUDE.md` |
| `app` | Public BFF | `apps/app/CLAUDE.md` (when it exists) |
| `admin` | Admin BFF | `apps/admin/CLAUDE.md` (when it exists) |
| `web` | Legacy Laravel | `apps/web/CLAUDE.md` |
| `contracts` | API specs and guides | `packages/contracts/docs/CLAUDE.md`, `packages/contracts/docs/guides/*.md` |

### Features (load cross-module context)

| Target | Description |
|--------|-------------|
| `auth` | Authentication across all modules |
| `tracker` | Career tracker |
| `challenges` | Challenges system |
| `database` | Players, clubs, leagues |
| `usage` | Limits/usage system |
| `social` | Social hub (future) |

### Migration (WEB -> APP context)

| Target | Description |
|--------|-------------|
| `migrate:auth` | Migrate auth from WEB to APP |
| `migrate:dashboard` | Migrate dashboard |
| `migrate:challenges` | Migrate challenges management |
| `migrate:tracker` | Migrate career tracker |
| `migrate:database` | Migrate player browsing |
| `migrate:settings` | Migrate configuration |
| `migrate:checkout` | Migrate payment flow |

---

## What to do after loading context

1. **Read the indicated files** using the Read tool
2. **Understand conventions** before making changes
3. **Follow the rules** in the corresponding CLAUDE.md
4. **Ask if there are doubts** before modifying existing contracts

---

## File mapping by feature

### auth
```
API:
- apps/api/app/Http/Controllers/V1/AuthController.php
- apps/api/app/Http/Requests/Auth/
- apps/api/app/Services/AuthService.php
- packages/contracts/docs/guides/auth.md

Mobile:
- apps/mobile/lib/features/auth/

Web (legacy):
- apps/web/app/Http/Controllers/Auth/
- apps/web/resources/js/Pages/Auth/
```

### database
```
API:
- apps/api/app/Database/Controllers/
- apps/api/app/Database/Data/
- apps/api/app/Database/Filters/
- packages/contracts/docs/guides/game-context.md
- packages/contracts/docs/guides/pagination.md

Mobile:
- apps/mobile/lib/features/database/
```

### usage
```
API:
- apps/api/app/Services/Usage.php (current, to be replaced)
- apps/api/app/Models/Plan.php
- apps/api/app/Models/UserUsage.php

Docs:
- docs/plans/2026-01-06-usage-system-v2-design.md
```

---

## Usage Example

```
User: /context-load api
Claude: [Reads apps/api/CLAUDE.md and packages/contracts/docs/CLAUDE.md]
        API context loaded. Main conventions:
        - JSON: camelCase
        - DTOs: Spatie Data with CamelCaseMapper
        - Pagination: cursor-based
        - Form Requests: use TransformsCamelCaseInput

User: /context-load migrate:auth
Claude: [Reads WEB and API files related to auth]
        Auth migration context loaded.

        WEB (legacy):
        - Controllers in apps/web/app/Http/Controllers/Auth/
        - Views in apps/web/resources/js/Pages/Auth/
        - Uses direct DB sessions

        APP (target):
        - Must use session + API token
        - Available endpoints: /auth/login, /auth/register, /auth/social

        Key differences:
        - WEB validates directly against DB
        - APP must call API and save token in session
```
