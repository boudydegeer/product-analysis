# GitHub Actions Feature Analysis Test

This document explains how to use the GitHub Actions workflow for automated feature analysis using Claude Agent SDK.

## Overview

The workflow (`analyze-feature.yml`) provides an automated way to analyze feature requests using Claude AI. It generates structured insights including complexity estimates, affected modules, implementation tasks, and technical risks.

## How to Trigger the Workflow

### Via GitHub UI

1. Navigate to your repository on GitHub
2. Click on the "Actions" tab
3. Select "Feature Analysis with Claude Agent SDK" from the workflow list
4. Click "Run workflow" button
5. Fill in the required inputs:
   - **feature_id**: Unique identifier (e.g., `FEAT-123`, `collaboration-dashboard`)
   - **feature_description**: Either paste the description directly OR provide a path to a markdown file (e.g., `experiments/sample-feature.md`)
   - **callback_url**: (Optional) URL to POST results to (e.g., `https://api.yourservice.com/features/analysis`)
6. Click "Run workflow"

### Via GitHub CLI

```bash
gh workflow run analyze-feature.yml \
  -f feature_id="FEAT-123" \
  -f feature_description="experiments/sample-feature.md" \
  -f callback_url="https://api.example.com/webhook"
```

### Via GitHub API

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/analyze-feature.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "feature_id": "FEAT-123",
      "feature_description": "experiments/sample-feature.md",
      "callback_url": "https://api.example.com/webhook"
    }
  }'
```

## Required Setup

### 1. Add ANTHROPIC_API_KEY Secret

Before running the workflow, you must add your Anthropic API key as a GitHub secret:

1. Go to your repository Settings
2. Navigate to "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key (starts with `sk-ant-...`)
6. Click "Add secret"

### 2. Enable GitHub Actions

Ensure GitHub Actions are enabled for your repository:
- Settings → Actions → General → "Allow all actions and reusable workflows"

## What the Workflow Validates

### 1. Feature Complexity Analysis
- **Story Points**: Fibonacci scale estimation (1, 2, 3, 5, 8, 13, 21)
- **Estimated Hours**: Time required for implementation
- **Complexity Level**: Low, Medium, High, or Very High
- **Rationale**: Explanation for the complexity assessment

### 2. Affected Modules Identification
- **File Paths**: Specific files or modules requiring changes
- **Change Type**: New files, modifications, or deletions
- **Reasoning**: Why each module is affected

### 3. Implementation Task Breakdown
- **Task Descriptions**: Specific, actionable implementation steps
- **Effort Estimates**: Hours per task
- **Dependencies**: Task dependencies and ordering
- **Priority Levels**: High, medium, or low priority

### 4. Technical Risk Assessment
- **Risk Categories**: Security, performance, compatibility, dependencies
- **Severity Levels**: Low, medium, high, or critical
- **Mitigation Strategies**: How to address each risk

### 5. Implementation Recommendations
- **Suggested Approach**: Recommended implementation strategy
- **Alternatives**: Other approaches to consider
- **Testing Strategy**: How to validate the implementation
- **Deployment Notes**: Deployment considerations

## Output Structure

The workflow produces a JSON file with the following structure:

```json
{
  "feature_id": "FEAT-123",
  "complexity": {
    "story_points": 13,
    "estimated_hours": 120,
    "level": "High",
    "rationale": "Complex real-time synchronization logic..."
  },
  "affected_modules": [
    {
      "path": "src/components/Dashboard.tsx",
      "change_type": "modify",
      "reason": "Add real-time data binding"
    }
  ],
  "implementation_tasks": [
    {
      "id": "task-1",
      "description": "Set up WebSocket server infrastructure",
      "estimated_effort_hours": 16,
      "dependencies": [],
      "priority": "high"
    }
  ],
  "technical_risks": [
    {
      "category": "performance",
      "description": "Real-time sync may cause high server load",
      "severity": "high",
      "mitigation": "Implement rate limiting and connection pooling"
    }
  ],
  "recommendations": {
    "approach": "Incremental rollout starting with presence indicators...",
    "alternatives": ["Polling-based updates", "Third-party services"],
    "testing_strategy": "Load testing with 50+ concurrent users",
    "deployment_notes": "Deploy WebSocket servers separately"
  },
  "metadata": {
    "analyzed_at": "2026-01-07T10:30:00Z",
    "workflow_run_id": "123456",
    "workflow_run_number": "42",
    "repository": "owner/repo",
    "actor": "username"
  }
}
```

## How Results Are Consumed

### 1. Workflow Artifacts

Results are automatically uploaded as workflow artifacts:
- **Artifact Name**: `feature-analysis-{feature_id}`
- **Retention**: 30 days
- **Access**: Download from the Actions run page

### 2. Workflow Summary

A summary is added to the GitHub Actions run:
- Key metrics displayed in the workflow UI
- Quick overview without downloading artifacts
- Links to full results

### 3. Callback URL (Optional)

If provided, results are POSTed to the callback URL:

**Request Headers:**
```
Content-Type: application/json
X-Feature-ID: {feature_id}
X-Workflow-Run-ID: {github_run_id}
```

**Request Body:**
The complete JSON analysis result (shown above)

### 4. Backend Integration Examples

#### Example 1: Webhook Endpoint
```javascript
// Express.js webhook handler
app.post('/api/features/analysis', async (req, res) => {
  const analysis = req.body;
  const featureId = req.headers['x-feature-id'];

  // Store in database
  await db.features.update(featureId, {
    complexity: analysis.complexity,
    tasks: analysis.implementation_tasks,
    risks: analysis.technical_risks,
    analyzed_at: analysis.metadata.analyzed_at
  });

  // Notify team
  await notificationService.send({
    title: `Feature ${featureId} analyzed`,
    message: `Complexity: ${analysis.complexity.level}, Tasks: ${analysis.implementation_tasks.length}`
  });

  res.json({ status: 'received' });
});
```

#### Example 2: Polling for Artifacts
```javascript
// Poll GitHub API for workflow results
async function getAnalysisResults(featureId) {
  const runs = await octokit.actions.listWorkflowRuns({
    owner: 'your-org',
    repo: 'your-repo',
    workflow_id: 'analyze-feature.yml'
  });

  // Find run for this feature
  const run = runs.data.workflow_runs.find(r =>
    r.name.includes(featureId) && r.status === 'completed'
  );

  if (!run) return null;

  // Download artifact
  const artifacts = await octokit.actions.listWorkflowRunArtifacts({
    owner: 'your-org',
    repo: 'your-repo',
    run_id: run.id
  });

  const artifact = artifacts.data.artifacts.find(a =>
    a.name === `feature-analysis-${featureId}`
  );

  if (!artifact) return null;

  // Download and parse
  const download = await octokit.actions.downloadArtifact({
    owner: 'your-org',
    repo: 'your-repo',
    artifact_id: artifact.id,
    archive_format: 'zip'
  });

  return parseArtifactZip(download.data);
}
```

#### Example 3: GraphQL Integration
```graphql
mutation UpdateFeatureAnalysis($input: FeatureAnalysisInput!) {
  updateFeatureAnalysis(input: $input) {
    feature {
      id
      complexity {
        storyPoints
        estimatedHours
        level
      }
      implementationTasks {
        id
        description
        estimatedEffortHours
        priority
      }
      technicalRisks {
        category
        description
        severity
      }
    }
  }
}
```

## Testing the Workflow

### Test with Sample Feature

1. Use the provided sample feature:
   ```bash
   gh workflow run analyze-feature.yml \
     -f feature_id="TEST-001" \
     -f feature_description="experiments/sample-feature.md"
   ```

2. Monitor the workflow execution in the Actions tab

3. Download the artifact when complete

4. Verify the JSON structure and content quality

### Test with Direct Description

```bash
gh workflow run analyze-feature.yml \
  -f feature_id="TEST-002" \
  -f feature_description="Add a dark mode toggle to the application settings page. Should persist user preference and switch between light and dark themes smoothly."
```

### Test with Callback URL

Use a webhook testing service like webhook.site:

1. Go to https://webhook.site and copy your unique URL
2. Run workflow:
   ```bash
   gh workflow run analyze-feature.yml \
     -f feature_id="TEST-003" \
     -f feature_description="experiments/sample-feature.md" \
     -f callback_url="https://webhook.site/YOUR-UNIQUE-ID"
   ```
3. Check webhook.site to see the posted results

## Troubleshooting

### Common Issues

1. **Workflow fails with "ANTHROPIC_API_KEY not found"**
   - Ensure the secret is added correctly in repository settings
   - Secret name must be exactly `ANTHROPIC_API_KEY`

2. **Claude Agent SDK installation fails**
   - Check npm registry accessibility
   - Verify Node.js version compatibility (requires Node 20+)

3. **Analysis produces no structured output**
   - Claude may not have formatted response as JSON
   - Check raw_output field in results
   - Review workflow logs for Claude's response

4. **Callback URL post fails**
   - Verify URL is accessible from GitHub Actions runners
   - Check endpoint accepts POST requests
   - Ensure no firewall blocking GitHub IPs

5. **File path not found**
   - Use repository-relative paths (e.g., `experiments/sample-feature.md`)
   - Ensure file exists in the repository
   - Check file was committed to the branch being analyzed

## Performance Considerations

- **Timeout**: Workflow has 15-minute timeout
- **Concurrency**: Multiple workflows can run in parallel
- **Rate Limits**:
  - Anthropic API: Check your account limits
  - GitHub Actions: Depends on your plan
- **Cost**:
  - Anthropic API usage charged per token
  - GitHub Actions minutes (free tier available)

## Security Notes

1. **API Key Protection**: Never commit API keys to repository
2. **Callback URLs**: Validate and sanitize in your backend
3. **Input Validation**: Feature descriptions are sent to Claude - avoid sensitive data
4. **Artifact Access**: Anyone with repo access can download artifacts

## Future Enhancements

Potential improvements for the workflow:

1. **Caching**: Cache Claude responses for identical feature descriptions
2. **Cost Tracking**: Add cost estimation and tracking
3. **Multi-Model**: Support different Claude models (Opus, Sonnet, Haiku)
4. **Batch Analysis**: Analyze multiple features in one workflow run
5. **Integration Tests**: Automatically validate against actual codebase
6. **Comparison**: Compare analysis with previous versions of the same feature
7. **Notifications**: Slack/email notifications when analysis completes
8. **Custom Prompts**: Allow custom analysis prompts via workflow inputs

## Support

For issues or questions:
- Check workflow logs in GitHub Actions tab
- Review this documentation
- Consult [Claude Agent SDK documentation](https://docs.anthropic.com/agent-sdk)
- Check [GitHub Actions documentation](https://docs.github.com/en/actions)
