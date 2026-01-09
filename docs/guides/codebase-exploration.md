# Codebase Exploration Guide

## Overview

The codebase exploration tool enables AI agents to understand the technical context of the repository by exploring files, patterns, and architecture through GitHub Actions.

## How It Works

1. **Tool Definition**: The `explore_codebase` tool is registered in the database and assigned to the brainstorm agent
2. **Triggering**: When an agent calls `explore_codebase`, the backend:
   - Creates a `CodebaseExploration` record
   - Triggers the `explore-codebase.yml` GitHub workflow
   - Sends a `tool_executing` WebSocket message to frontend
3. **Exploration**: The GitHub Action:
   - Runs Claude Agent SDK with read_file, list_directory, search_files tools
   - Explores based on scope (full/backend/frontend) and focus (patterns/files/architecture/dependencies)
   - Saves structured results to artifact
4. **Results**: The polling service:
   - Checks workflow status every 30 seconds
   - Downloads results when complete
   - Formats context for agent injection
5. **Context Injection**: Results are formatted as markdown and provided back to the agent

## Tool Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | What to explore (e.g., "How is auth implemented?") |
| scope | enum | No | "full" | Which part to explore: full, backend, frontend |
| focus | enum | No | "patterns" | What to focus on: patterns, files, architecture, dependencies |

## Example Usage

In a brainstorm conversation, the agent might call:

```json
{
  "tool": "explore_codebase",
  "input": {
    "query": "How is the database schema structured?",
    "scope": "backend",
    "focus": "architecture"
  }
}
```

## Output Format

The exploration returns structured JSON with:

- **summary**: Brief overview of findings
- **relevant_files**: List of relevant files found
- **key_patterns**: Patterns identified in the code
- **code_examples**: Relevant code snippets with explanations
- **architecture_notes**: Notes about system architecture
- **dependencies**: External dependencies identified
- **recommendations**: Actionable recommendations
- **confidence**: high/medium/low confidence level

## Configuration

### Environment Variables

- `WEBHOOK_BASE_URL`: If set, results are POSTed directly; otherwise polling is used
- `ANALYSIS_POLLING_INTERVAL_SECONDS`: Polling interval (default: 30)
- `ANALYSIS_POLLING_TIMEOUT_SECONDS`: Timeout for explorations (default: 900)

### GitHub Secrets

- `ANTHROPIC_API_KEY`: Required for Claude Agent SDK in the workflow

## Database Schema

```sql
CREATE TABLE codebase_explorations (
  id VARCHAR(50) PRIMARY KEY,
  session_id VARCHAR(50),
  message_id VARCHAR(50),
  query TEXT NOT NULL,
  scope VARCHAR(20) DEFAULT 'full',
  focus VARCHAR(20) DEFAULT 'patterns',
  workflow_run_id VARCHAR(50),
  workflow_url VARCHAR(500),
  status codebaseexplorationstatus NOT NULL,
  results JSONB,
  formatted_context TEXT,
  error_message TEXT,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

## Troubleshooting

### Exploration stuck in INVESTIGATING

- Check GitHub Actions for workflow status
- Verify `ANTHROPIC_API_KEY` is set in repository secrets
- Check polling service is running (`poll_pending_explorations` task)

### No results returned

- Check workflow artifact was created
- Verify artifact name matches expected pattern (`exploration-results-{id}`)
- Check for errors in workflow logs

### Context not appearing in agent

- Verify `formatted_context` is populated in database
- Check WebSocket connection is active
- Look for errors in browser console
