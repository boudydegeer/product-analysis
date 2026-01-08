# Plan Status Management Script Guide

## Overview

The `update-plan-status.js` script manages plan status tracking in the `docs/plans/index.md` file. It provides commands to register new plans, update their status, and list all plans with automatic statistics calculation.

## Features

1. **Register new plans** - Add new plans to the index with initial status
2. **Update plan status** - Move plans between status sections
3. **Automatic statistics** - Recalculates counts and percentages after changes
4. **Changelog tracking** - Appends entries to the change log section
5. **Date updates** - Updates "Last Updated" date automatically
6. **List plans** - Display all plans grouped by status

## Valid Statuses

| Status | Emoji | Description |
|--------|-------|-------------|
| `backlog` | 🔴 | Not started, planned for future |
| `ready` | 🟢 | Ready to start implementation |
| `in-progress` | 🟡 | Currently being implemented |
| `for-review` | 🔵 | Implemented, needs testing/review |
| `done` | ✅ | Completed and verified |
| `blocked` | 🚫 | Blocked by dependencies or issues |

## Commands

### Register a New Plan

Adds a new plan to the index with the specified initial status.

```bash
node scripts/update-plan-status.js --register \
  --file=<filename> \
  --title="<plan title>" \
  --description="<brief description>" \
  --status=<status>
```

**Example:**
```bash
node scripts/update-plan-status.js --register \
  --file=2026-01-08-auth-module.md \
  --title="Authentication Module" \
  --description="User authentication system with JWT tokens" \
  --status=backlog
```

**Required Arguments:**
- `--file` - Plan filename (e.g., `2026-01-08-feature-name.md`)
- `--title` - Plan title (displayed in the index)
- `--description` - Brief description of the plan
- `--status` - Initial status (one of: backlog, ready, in-progress, for-review, done, blocked)

**What happens:**
- Plan is added to the appropriate status section in index.md
- Statistics are automatically recalculated
- "Last Updated" date is updated
- Changelog entry is added

### Update Plan Status

Moves a plan from one status to another.

```bash
node scripts/update-plan-status.js --update \
  --file=<filename> \
  --status=<new-status> \
  [--note="<optional note>"]
```

**Examples:**

```bash
# Move to ready status
node scripts/update-plan-status.js --update \
  --file=2026-01-08-auth-module.md \
  --status=ready \
  --note="Plan completed and reviewed"

# Start implementation
node scripts/update-plan-status.js --update \
  --file=2026-01-08-auth-module.md \
  --status=in-progress

# Move to review
node scripts/update-plan-status.js --update \
  --file=2026-01-08-auth-module.md \
  --status=for-review \
  --note="Implementation complete, ready for review"

# Mark as done
node scripts/update-plan-status.js --update \
  --file=2026-01-08-auth-module.md \
  --status=done \
  --note="All tasks completed, tested, and deployed"

# Mark as blocked
node scripts/update-plan-status.js --update \
  --file=2026-01-08-auth-module.md \
  --status=blocked \
  --note="Waiting for external API documentation"
```

**Required Arguments:**
- `--file` - Plan filename (must already exist in index)
- `--status` - New status

**Optional Arguments:**
- `--note` - Additional note to add to the plan and changelog

**What happens:**
- Plan is moved from current section to new status section
- Status emoji and label are updated in the plan entry
- Note is added to the plan entry (if provided)
- Statistics are automatically recalculated
- "Last Updated" date is updated
- Changelog entry is added with status transition

### List All Plans

Displays all plans grouped by status with their filenames.

```bash
node scripts/update-plan-status.js --list
```

**Example Output:**
```
📋 All Plans

================================================================================

✅ Done (2)
--------------------------------------------------------------------------------
  • MVP Implementation Plan
    File: 2026-01-07-product-analysis-platform-mvp.md
  • Dual Mechanism for Workflow Results
    File: 2026-01-07-workflow-results-dual-mechanism.md

🟡 In Progress (1)
--------------------------------------------------------------------------------
  • Authentication Module
    File: 2026-01-08-auth-module.md

🔴 Backlog (1)
--------------------------------------------------------------------------------
  • Product Analysis Platform - Full Design
    File: 2026-01-07-product-analysis-platform-design.md

================================================================================
Total Plans: 4
```

### Show Help

Displays usage information and examples.

```bash
node scripts/update-plan-status.js --help
# or
node scripts/update-plan-status.js -h
```

## Typical Workflow

Here's a typical workflow for managing a plan from start to finish:

```bash
# 1. Register a new plan in backlog
node scripts/update-plan-status.js --register \
  --file=2026-01-08-payment-integration.md \
  --title="Payment Integration" \
  --description="Integrate Stripe payment processing" \
  --status=backlog

# 2. Create the actual plan document
# (Write the plan in docs/plans/2026-01-08-payment-integration.md)

# 3. Move to ready when plan is complete
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=ready \
  --note="Plan reviewed and approved"

# 4. Start implementation
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=in-progress

# 5. If blocked during implementation
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=blocked \
  --note="Waiting for Stripe API keys from DevOps"

# 6. Resume when unblocked
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=in-progress \
  --note="API keys received, resuming work"

# 7. Move to review when implementation is done
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=for-review \
  --note="Implementation complete, all tests passing"

# 8. Mark as done after review
node scripts/update-plan-status.js --update \
  --file=2026-01-08-payment-integration.md \
  --status=done \
  --note="Reviewed, tested, and deployed to production"

# 9. Check all plans
node scripts/update-plan-status.js --list
```

## What Gets Updated

When you register or update a plan, the script automatically updates:

1. **Plan Sections** - Moves or adds plan entries in the appropriate status section
2. **Status Emoji** - Updates the emoji next to the plan status
3. **Statistics Table** - Recalculates counts and percentages for all statuses
4. **Last Updated Date** - Updates to current date (YYYY-MM-DD format)
5. **Changelog** - Adds a timestamped entry with the change details

## Error Handling

The script includes comprehensive error handling:

**Invalid Status:**
```bash
$ node scripts/update-plan-status.js --update --file=plan.md --status=invalid
Error: Invalid status 'invalid'. Valid statuses: backlog, ready, in-progress, for-review, done, blocked
```

**Plan Not Found:**
```bash
$ node scripts/update-plan-status.js --update --file=nonexistent.md --status=done
Error: Plan 'nonexistent.md' not found
```

**Duplicate Registration:**
```bash
$ node scripts/update-plan-status.js --register --file=existing.md --title="Test" --description="Test" --status=backlog
Warning: Plan 'existing.md' already exists with status 'done'
Use --update to change its status
```

**Missing Required Arguments:**
```bash
$ node scripts/update-plan-status.js --register --file=plan.md
Error: --title is required for registration
```

## Requirements

- **Node.js** v14+ with ESM module support
- **No external dependencies** - uses only Node.js built-ins (fs, path, url)
- Script is executable: `chmod +x scripts/update-plan-status.js`

## Technical Details

### File Structure

The script expects `docs/plans/index.md` to have this structure:

```markdown
# Product Analysis Platform - Plans Index

**Last Updated:** YYYY-MM-DD

## 📋 Plans Overview
...

## ✅ Done
### [Plan Title](./plan-file.md)
**Status:** ✅ Done
**Description:** Plan description
...

## 🔵 For Review
...

## 🟡 In Progress
...

## 🟢 Ready
...

## 🚫 Blocked
...

## 🔴 Backlog
...

## 📊 Summary Statistics
...

## 📝 Change Log
...
```

### Missing Sections

If a status section doesn't exist in the index, the script will automatically create it when needed. Sections are always rendered in this order:

1. Done
2. For Review
3. In Progress
4. Ready
5. Blocked
6. Backlog

### Changelog Format

Changelog entries are added with this format:

```markdown
### YYYY-MM-DD
- 🟡 Updated [Plan Title](./plan-file.md): Ready → In Progress - Optional note
- 🔴 Registered new plan: [Plan Title](./plan-file.md) as Backlog
```

If there's already an entry for today's date, new entries are added under that date header.

## Best Practices

1. **Use descriptive titles** - Plan titles appear in lists and changelogs
2. **Add notes for status changes** - Helps track progress and blockers
3. **Follow naming conventions** - Use format: `YYYY-MM-DD-feature-name.md`
4. **Update status regularly** - Keep the index in sync with actual work
5. **Use blocked status** - Document blockers instead of keeping plans in progress
6. **List plans regularly** - Use `--list` to get an overview of all work

## Integration Examples

### Git Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Ensure plan index is updated before commit
if git diff --cached --name-only | grep -q "docs/plans/.*\.md"; then
    echo "Plan files changed. Remember to update status with:"
    echo "  node scripts/update-plan-status.js --update --file=<file> --status=<status>"
fi
```

### CI/CD Pipeline

In GitHub Actions:

```yaml
- name: Verify plan index is up to date
  run: |
    node scripts/update-plan-status.js --list
    git diff --exit-code docs/plans/index.md || \
      (echo "Plan index has uncommitted changes" && exit 1)
```

### Makefile

```makefile
.PHONY: plan-list
plan-list:
	node scripts/update-plan-status.js --list

.PHONY: plan-register
plan-register:
	@read -p "Filename: " FILE; \
	read -p "Title: " TITLE; \
	read -p "Description: " DESC; \
	read -p "Status (backlog/ready/in-progress/for-review/done/blocked): " STATUS; \
	node scripts/update-plan-status.js --register \
		--file=$$FILE --title="$$TITLE" --description="$$DESC" --status=$$STATUS
```

## Troubleshooting

**Script not executable:**
```bash
chmod +x scripts/update-plan-status.js
```

**Node version issues:**
```bash
# Check Node version (need v14+)
node --version

# Or run with node explicitly
node scripts/update-plan-status.js --help
```

**Index file not found:**
The script expects the index at `docs/plans/index.md` relative to the project root. Make sure you're running from the correct directory.

**Unexpected formatting:**
The script preserves most of the index content but reformats the status sections. If you have custom content in status sections, it will be lost. Keep custom content in other sections like "Technical Debt & Improvements" or "Related Documentation".

## Support

For issues or questions:
1. Check this guide first
2. Run with `--help` for quick reference
3. Check the source code comments for technical details
4. Test with `--list` before and after changes

---

*Last updated: 2026-01-08*
