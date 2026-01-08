# Analysis Details UI Design Specification

**Date:** 2026-01-08
**Status:** Design Complete
**Priority:** High

## Overview

This document specifies the design for displaying AI-generated feature analysis in the dashboard. The design introduces a four-tab interface that presents analysis results organized by concern: overview, implementation details, risks, and recommendations.

## Architecture

### System Flow

```
User clicks feature row
    ↓
Dashboard fetches analysis via API
    ↓
UI displays 4-tab interface:
- Overview (technical summary + metrics)
- Implementation (architecture + technical details)
- Risks & Warnings (concerns + mitigations)
- Recommendations (actionable improvements)
```

### Data Flow

```
Frontend (Vue) → API Request → Backend (FastAPI) → Database (PostgreSQL)
                                      ↓
                              JSON Response (flattened)
                                      ↓
                              Vue Components Render
```

## Database Schema Changes

### Flatten Nested Structure

Current schema stores analysis in nested JSON. Flatten this structure to improve query performance and simplify access patterns.

#### Before (Nested)
```json
{
  "analysis_result": {
    "summary": {
      "overview": "...",
      "key_points": [],
      "metrics": {}
    },
    "implementation": {
      "architecture": {},
      "technical_details": []
    }
  }
}
```

#### After (Flattened)
```json
{
  "summary_overview": "...",
  "summary_key_points": [],
  "summary_metrics": {},
  "implementation_architecture": {},
  "implementation_technical_details": []
}
```

### Migration Steps

1. **Create migration script**: `alembic revision --autogenerate -m "flatten_analysis_result_structure"`
2. **Add new columns**: Create individual columns for each flattened field
3. **Migrate data**: Extract nested values into new columns
4. **Update models**: Modify SQLAlchemy models to match new schema
5. **Remove old column**: Drop `analysis_result` after confirming data integrity

### Schema Definition

```sql
ALTER TABLE features
  ADD COLUMN summary_overview TEXT,
  ADD COLUMN summary_key_points JSONB,
  ADD COLUMN summary_metrics JSONB,
  ADD COLUMN implementation_architecture JSONB,
  ADD COLUMN implementation_technical_details JSONB,
  ADD COLUMN implementation_data_flow JSONB,
  ADD COLUMN risks_technical_risks JSONB,
  ADD COLUMN risks_security_concerns JSONB,
  ADD COLUMN risks_scalability_issues JSONB,
  ADD COLUMN risks_mitigation_strategies JSONB,
  ADD COLUMN recommendations_improvements JSONB,
  ADD COLUMN recommendations_best_practices JSONB,
  ADD COLUMN recommendations_next_steps JSONB;
```

## API Endpoint Design

### Endpoint

```
GET /api/v1/features/{feature_id}/analysis
```

### Response Format

Return flattened analysis structure. Group related fields under top-level keys that match tab names.

```json
{
  "feature_id": "abc123",
  "feature_name": "User Authentication",
  "analyzed_at": "2026-01-08T10:30:00Z",
  "status": "completed",

  "overview": {
    "summary": "This feature implements JWT-based authentication...",
    "key_points": [
      "Uses JWT tokens with 24-hour expiration",
      "Implements refresh token rotation",
      "Supports OAuth2 providers (Google, GitHub)"
    ],
    "metrics": {
      "complexity": "medium",
      "estimated_effort": "3-5 days",
      "confidence": 0.85
    }
  },

  "implementation": {
    "architecture": {
      "pattern": "Token-based authentication with refresh mechanism",
      "components": [
        "AuthService: Token generation and validation",
        "AuthMiddleware: Request authentication",
        "RefreshService: Token rotation"
      ]
    },
    "technical_details": [
      {
        "category": "Authentication",
        "description": "JWT tokens signed with RS256 algorithm",
        "code_locations": ["/auth/jwt.py", "/middleware/auth.py"]
      }
    ],
    "data_flow": {
      "description": "Login → Generate Token → Store Refresh → Return Access",
      "steps": [
        "User provides credentials",
        "System validates against database",
        "System generates JWT access token",
        "System generates refresh token",
        "System returns both tokens to client"
      ]
    }
  },

  "risks": {
    "technical_risks": [
      {
        "severity": "high",
        "category": "Security",
        "description": "Token stored in localStorage vulnerable to XSS",
        "impact": "Attacker could steal authentication tokens"
      }
    ],
    "security_concerns": [
      {
        "severity": "medium",
        "description": "No rate limiting on login endpoint",
        "cwe": "CWE-307: Improper Restriction of Excessive Authentication Attempts"
      }
    ],
    "scalability_issues": [
      {
        "severity": "low",
        "description": "Token validation requires database lookup on every request",
        "recommendation": "Implement Redis cache for token validation"
      }
    ],
    "mitigation_strategies": [
      "Store tokens in httpOnly cookies instead of localStorage",
      "Implement rate limiting using Redis",
      "Add token validation caching"
    ]
  },

  "recommendations": {
    "improvements": [
      {
        "priority": "high",
        "title": "Implement httpOnly cookie storage",
        "description": "Move token storage from localStorage to httpOnly cookies to prevent XSS attacks",
        "effort": "1-2 days"
      }
    ],
    "best_practices": [
      "Implement CSRF protection for cookie-based auth",
      "Add security headers (HSTS, CSP)",
      "Use short-lived access tokens (15 min) with refresh mechanism"
    ],
    "next_steps": [
      "Conduct security audit of authentication flow",
      "Implement rate limiting and monitoring",
      "Add multi-factor authentication support"
    ]
  }
}
```

### Error States

```json
// No analysis exists
{
  "feature_id": "abc123",
  "status": "no_analysis",
  "message": "No analysis available for this feature"
}

// Analysis failed
{
  "feature_id": "abc123",
  "status": "failed",
  "message": "Analysis failed: API timeout",
  "failed_at": "2026-01-08T10:30:00Z"
}

// Analysis in progress
{
  "feature_id": "abc123",
  "status": "analyzing",
  "message": "Analysis in progress...",
  "started_at": "2026-01-08T10:28:00Z"
}
```

## UI Design

### Layout Structure

Use shadcn-vue Tabs component for main navigation. Display full-width content area with consistent spacing.

```
┌─────────────────────────────────────────────────────────────┐
│ Feature: User Authentication                      [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Overview ─┬─ Implementation ─┬─ Risks & Warnings ─┬─ Recommendations ─┐
│ │                                                            │
│ │ [Tab Content Area - Full Width]                           │
│ │                                                            │
│ │                                                            │
│ └────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### Tab 1: Overview

Display executive summary with key metrics and highlights.

#### Components

**Summary Section**
- Use `<Card>` with `<CardHeader>` and `<CardContent>`
- Display `overview.summary` as main text
- Style: `text-base leading-relaxed text-muted-foreground`

**Key Points Section**
- Header: "Key Points" with `text-lg font-semibold`
- Render `overview.key_points` as bulleted list
- Use check circle icons before each point
- Style: `space-y-2`

**Metrics Grid**
- Use 3-column grid: `grid grid-cols-3 gap-4`
- Each metric in separate card with:
  - Label (top, muted)
  - Value (large, bold)
  - Visual indicator (badge or icon)

**Complexity Badge Colors**
- Low: `bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300`
- Medium: `bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300`
- High: `bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300`

#### Layout

```vue
<TabsContent value="overview" class="space-y-6">
  <!-- Summary Card -->
  <Card>
    <CardHeader>
      <CardTitle>Summary</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="text-base leading-relaxed text-muted-foreground">
        {{ analysis.overview.summary }}
      </p>
    </CardContent>
  </Card>

  <!-- Key Points -->
  <Card>
    <CardHeader>
      <CardTitle>Key Points</CardTitle>
    </CardHeader>
    <CardContent>
      <ul class="space-y-2">
        <li v-for="point in analysis.overview.key_points"
            class="flex items-start gap-2">
          <CheckCircle2 class="w-5 h-5 text-green-600 mt-0.5" />
          <span>{{ point }}</span>
        </li>
      </ul>
    </CardContent>
  </Card>

  <!-- Metrics Grid -->
  <div class="grid grid-cols-3 gap-4">
    <Card>
      <CardHeader>
        <CardDescription>Complexity</CardDescription>
      </CardHeader>
      <CardContent>
        <Badge :class="complexityColor">
          {{ analysis.overview.metrics.complexity }}
        </Badge>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardDescription>Estimated Effort</CardDescription>
      </CardHeader>
      <CardContent>
        <p class="text-2xl font-bold">
          {{ analysis.overview.metrics.estimated_effort }}
        </p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardDescription>Confidence</CardDescription>
      </CardHeader>
      <CardContent>
        <p class="text-2xl font-bold">
          {{ (analysis.overview.metrics.confidence * 100).toFixed(0) }}%
        </p>
      </CardContent>
    </Card>
  </div>
</TabsContent>
```

### Tab 2: Implementation

Display technical architecture, components, and data flow.

#### Sections

**Architecture Pattern**
- Card with title "Architecture Pattern"
- Display `implementation.architecture.pattern` as primary text
- List components below with monospace font

**Technical Details**
- Group by category
- Use `<Accordion>` for collapsible sections
- Each detail shows:
  - Category badge
  - Description
  - Code locations as clickable links (if available)

**Data Flow Diagram**
- Card with title "Data Flow"
- Display `implementation.data_flow.description` as overview
- Render steps as vertical flow:

```
  Step 1: User provides credentials
    ↓
  Step 2: System validates against database
    ↓
  Step 3: System generates JWT access token
    ↓
  ...
```

#### Layout

```vue
<TabsContent value="implementation" class="space-y-6">
  <!-- Architecture -->
  <Card>
    <CardHeader>
      <CardTitle>Architecture Pattern</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <p class="text-base">{{ implementation.architecture.pattern }}</p>

      <div>
        <h4 class="text-sm font-semibold mb-2">Components</h4>
        <ul class="space-y-1 font-mono text-sm">
          <li v-for="component in implementation.architecture.components">
            {{ component }}
          </li>
        </ul>
      </div>
    </CardContent>
  </Card>

  <!-- Technical Details -->
  <Card>
    <CardHeader>
      <CardTitle>Technical Details</CardTitle>
    </CardHeader>
    <CardContent>
      <Accordion type="single" collapsible>
        <AccordionItem v-for="detail in implementation.technical_details"
                       :value="detail.category">
          <AccordionTrigger>
            <Badge variant="outline">{{ detail.category }}</Badge>
          </AccordionTrigger>
          <AccordionContent class="space-y-2">
            <p>{{ detail.description }}</p>
            <div v-if="detail.code_locations">
              <p class="text-sm text-muted-foreground">Code locations:</p>
              <ul class="text-sm font-mono">
                <li v-for="location in detail.code_locations">
                  {{ location }}
                </li>
              </ul>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </CardContent>
  </Card>

  <!-- Data Flow -->
  <Card>
    <CardHeader>
      <CardTitle>Data Flow</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <p class="text-base">{{ implementation.data_flow.description }}</p>

      <div class="space-y-2">
        <div v-for="(step, index) in implementation.data_flow.steps"
             class="flex items-start gap-3">
          <div class="flex flex-col items-center">
            <div class="w-8 h-8 rounded-full bg-primary text-primary-foreground
                        flex items-center justify-center text-sm font-semibold">
              {{ index + 1 }}
            </div>
            <div v-if="index < implementation.data_flow.steps.length - 1"
                 class="w-0.5 h-8 bg-border mt-1"></div>
          </div>
          <p class="pt-1">{{ step }}</p>
        </div>
      </div>
    </CardContent>
  </Card>
</TabsContent>
```

### Tab 3: Risks & Warnings

Display security concerns, technical risks, and mitigation strategies.

#### Components

**Severity Badges**
- Critical: `bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300`
- High: `bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300`
- Medium: `bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300`
- Low: `bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300`

**Risk Icons**
- Technical: `AlertTriangle` (yellow)
- Security: `Shield` (red)
- Scalability: `TrendingUp` (blue)

#### Sections

**Technical Risks**
- Display as Alert components with warning variant
- Show severity badge, category, and description
- Include impact statement if available

**Security Concerns**
- Use Alert component with destructive variant
- Highlight CWE numbers if present
- Include severity and mitigation

**Scalability Issues**
- Use Alert component with default variant
- Show severity and recommendations

**Mitigation Strategies**
- Display as checklist with action items
- Use Card component with accent border

#### Layout

```vue
<TabsContent value="risks" class="space-y-6">
  <!-- Technical Risks -->
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <AlertTriangle class="w-5 h-5 text-yellow-600" />
        Technical Risks
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <Alert v-for="risk in risks.technical_risks"
             variant="warning">
        <div class="flex items-start justify-between">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <Badge :class="severityColor(risk.severity)">
                {{ risk.severity }}
              </Badge>
              <Badge variant="outline">{{ risk.category }}</Badge>
            </div>
            <AlertDescription>{{ risk.description }}</AlertDescription>
            <p v-if="risk.impact" class="text-sm text-muted-foreground mt-2">
              Impact: {{ risk.impact }}
            </p>
          </div>
        </div>
      </Alert>
    </CardContent>
  </Card>

  <!-- Security Concerns -->
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <Shield class="w-5 h-5 text-red-600" />
        Security Concerns
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <Alert v-for="concern in risks.security_concerns"
             variant="destructive">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <Badge :class="severityColor(concern.severity)">
              {{ concern.severity }}
            </Badge>
            <Badge v-if="concern.cwe" variant="outline" class="font-mono">
              {{ concern.cwe }}
            </Badge>
          </div>
          <AlertDescription>{{ concern.description }}</AlertDescription>
        </div>
      </Alert>
    </CardContent>
  </Card>

  <!-- Scalability Issues -->
  <Card v-if="risks.scalability_issues?.length > 0">
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <TrendingUp class="w-5 h-5 text-blue-600" />
        Scalability Issues
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <Alert v-for="issue in risks.scalability_issues">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <Badge :class="severityColor(issue.severity)">
              {{ issue.severity }}
            </Badge>
          </div>
          <AlertDescription>{{ issue.description }}</AlertDescription>
          <p v-if="issue.recommendation"
             class="text-sm text-muted-foreground mt-2">
            Recommendation: {{ issue.recommendation }}
          </p>
        </div>
      </Alert>
    </CardContent>
  </Card>

  <!-- Mitigation Strategies -->
  <Card class="border-l-4 border-l-blue-500">
    <CardHeader>
      <CardTitle>Mitigation Strategies</CardTitle>
    </CardHeader>
    <CardContent>
      <ul class="space-y-2">
        <li v-for="strategy in risks.mitigation_strategies"
            class="flex items-start gap-2">
          <CheckCircle2 class="w-5 h-5 text-blue-600 mt-0.5" />
          <span>{{ strategy }}</span>
        </li>
      </ul>
    </CardContent>
  </Card>
</TabsContent>
```

### Tab 4: Recommendations

Display actionable improvements, best practices, and next steps.

#### Sections

**Priority Improvements**
- Sort by priority (high → medium → low)
- Display as cards with priority badge
- Show title, description, and effort estimate

**Priority Badge Colors**
- High: `bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300`
- Medium: `bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300`
- Low: `bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300`

**Best Practices**
- Display as checklist
- Use info icon before each item

**Next Steps**
- Display as numbered action items
- Style as timeline/roadmap

#### Layout

```vue
<TabsContent value="recommendations" class="space-y-6">
  <!-- Improvements -->
  <div>
    <h3 class="text-lg font-semibold mb-4">Priority Improvements</h3>
    <div class="space-y-4">
      <Card v-for="improvement in sortedImprovements">
        <CardHeader>
          <div class="flex items-start justify-between">
            <CardTitle class="text-base">{{ improvement.title }}</CardTitle>
            <Badge :class="priorityColor(improvement.priority)">
              {{ improvement.priority }}
            </Badge>
          </div>
        </CardHeader>
        <CardContent class="space-y-2">
          <p class="text-muted-foreground">{{ improvement.description }}</p>
          <div v-if="improvement.effort"
               class="flex items-center gap-2 text-sm">
            <Clock class="w-4 h-4" />
            <span>Estimated effort: {{ improvement.effort }}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>

  <!-- Best Practices -->
  <Card>
    <CardHeader>
      <CardTitle>Best Practices</CardTitle>
    </CardHeader>
    <CardContent>
      <ul class="space-y-2">
        <li v-for="practice in recommendations.best_practices"
            class="flex items-start gap-2">
          <Info class="w-5 h-5 text-blue-600 mt-0.5" />
          <span>{{ practice }}</span>
        </li>
      </ul>
    </CardContent>
  </Card>

  <!-- Next Steps -->
  <Card>
    <CardHeader>
      <CardTitle>Next Steps</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="space-y-3">
        <div v-for="(step, index) in recommendations.next_steps"
             class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-primary text-primary-foreground
                      flex items-center justify-center text-sm font-semibold shrink-0">
            {{ index + 1 }}
          </div>
          <p class="pt-1">{{ step }}</p>
        </div>
      </div>
    </CardContent>
  </Card>
</TabsContent>
```

## Special States

### Loading State

Display skeleton loaders while fetching analysis data.

```vue
<div class="space-y-6">
  <Card>
    <CardHeader>
      <Skeleton class="h-6 w-32" />
    </CardHeader>
    <CardContent>
      <Skeleton class="h-4 w-full mb-2" />
      <Skeleton class="h-4 w-3/4" />
    </CardContent>
  </Card>
</div>
```

### No Analysis State

Display when feature has no analysis yet.

```vue
<Card>
  <CardContent class="flex flex-col items-center justify-center py-12">
    <FileQuestion class="w-16 h-16 text-muted-foreground mb-4" />
    <h3 class="text-lg font-semibold mb-2">No Analysis Available</h3>
    <p class="text-muted-foreground text-center mb-4">
      This feature hasn't been analyzed yet.
    </p>
    <Button @click="requestAnalysis">
      <Sparkles class="w-4 h-4 mr-2" />
      Request Analysis
    </Button>
  </CardContent>
</Card>
```

### Failed Analysis State

Display when analysis failed with error message.

```vue
<Alert variant="destructive">
  <AlertCircle class="h-4 w-4" />
  <AlertTitle>Analysis Failed</AlertTitle>
  <AlertDescription>
    {{ error.message }}
  </AlertDescription>
  <Button variant="outline" class="mt-4" @click="retryAnalysis">
    <RefreshCw class="w-4 h-4 mr-2" />
    Retry Analysis
  </Button>
</Alert>
```

### Analyzing State

Display progress indicator while analysis runs.

```vue
<Card>
  <CardContent class="flex flex-col items-center justify-center py-12">
    <Loader2 class="w-16 h-16 text-primary animate-spin mb-4" />
    <h3 class="text-lg font-semibold mb-2">Analyzing Feature...</h3>
    <p class="text-muted-foreground text-center">
      This may take a few moments.
    </p>
    <p class="text-sm text-muted-foreground mt-2">
      Started {{ formatTimestamp(analysis.started_at) }}
    </p>
  </CardContent>
</Card>
```

### Partial Data State

Display available sections while indicating missing data.

```vue
<!-- Show available tabs normally -->
<TabsContent value="overview">
  <!-- Full content -->
</TabsContent>

<!-- Disabled tab with explanation -->
<TabsTrigger value="implementation" disabled>
  Implementation
  <Badge variant="outline" class="ml-2">Not Available</Badge>
</TabsTrigger>
```

## Integration with Feature Details View

### Opening Analysis

User clicks feature row in dashboard table → Trigger analysis view.

**Option A: Modal Dialog**
- Use shadcn-vue `<Dialog>` component
- Full-screen or large size
- Easy to dismiss, returns to table

**Option B: Side Panel**
- Use shadcn-vue `<Sheet>` component
- Slides from right
- Table remains visible

**Option C: Route Navigation**
- Navigate to `/features/{id}/analysis`
- Full page view
- Better for deep linking and sharing

**Recommendation:** Start with Modal Dialog (Option A) for quick access, add route navigation later for sharing.

### Modal Implementation

```vue
<Dialog v-model:open="showAnalysis">
  <DialogContent class="max-w-5xl max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>{{ feature.name }}</DialogTitle>
      <DialogDescription>
        Analyzed {{ formatTimestamp(analysis.analyzed_at) }}
      </DialogDescription>
    </DialogHeader>

    <Tabs default-value="overview" class="mt-6">
      <TabsList class="grid w-full grid-cols-4">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="implementation">Implementation</TabsTrigger>
        <TabsTrigger value="risks">Risks & Warnings</TabsTrigger>
        <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
      </TabsList>

      <!-- Tab contents as specified above -->
    </Tabs>
  </DialogContent>
</Dialog>
```

### State Management

Use Vue composable for analysis data and state.

```typescript
// composables/useFeatureAnalysis.ts
export function useFeatureAnalysis(featureId: string) {
  const analysis = ref<AnalysisResponse | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const fetchAnalysis = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/features/${featureId}/analysis`)
      analysis.value = await response.json()
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  const requestAnalysis = async () => {
    // Trigger new analysis
  }

  const retryAnalysis = async () => {
    await fetchAnalysis()
  }

  return {
    analysis,
    loading,
    error,
    fetchAnalysis,
    requestAnalysis,
    retryAnalysis
  }
}
```

## Component Structure

```
components/
├── analysis/
│   ├── AnalysisDialog.vue           # Main dialog wrapper
│   ├── AnalysisTabs.vue             # Tab container
│   ├── tabs/
│   │   ├── OverviewTab.vue          # Overview content
│   │   ├── ImplementationTab.vue    # Implementation content
│   │   ├── RisksTab.vue             # Risks content
│   │   └── RecommendationsTab.vue   # Recommendations content
│   ├── states/
│   │   ├── LoadingState.vue         # Loading skeleton
│   │   ├── NoAnalysisState.vue      # Empty state
│   │   ├── FailedState.vue          # Error state
│   │   └── AnalyzingState.vue       # In-progress state
│   └── shared/
│       ├── SeverityBadge.vue        # Reusable severity badge
│       ├── PriorityBadge.vue        # Reusable priority badge
│       └── ComplexityBadge.vue      # Reusable complexity badge
```

## Implementation Checklist

### Backend Tasks
- [ ] Create database migration for flattened schema
- [ ] Update SQLAlchemy models
- [ ] Migrate existing analysis data
- [ ] Implement GET `/api/v1/features/{feature_id}/analysis` endpoint
- [ ] Add error handling for missing/failed analysis
- [ ] Write endpoint tests

### Frontend Tasks
- [ ] Create analysis composable (`useFeatureAnalysis`)
- [ ] Build AnalysisDialog component
- [ ] Implement Overview tab
- [ ] Implement Implementation tab
- [ ] Implement Risks & Warnings tab
- [ ] Implement Recommendations tab
- [ ] Add loading/error/empty states
- [ ] Integrate with dashboard table
- [ ] Add responsive design for mobile
- [ ] Write component tests

### Design Tasks
- [ ] Validate badge colors in dark mode
- [ ] Test accessibility (keyboard navigation, screen readers)
- [ ] Verify responsive behavior on tablet/mobile
- [ ] Review copy and error messages

## Testing Strategy

### Unit Tests
- Test analysis composable with mock data
- Test each tab component in isolation
- Test state components (loading, error, empty)
- Test badge components with different values

### Integration Tests
- Test full analysis dialog flow
- Test tab switching and data display
- Test API error handling
- Test loading states

### E2E Tests
- Test opening analysis from dashboard
- Test navigation through all tabs
- Test requesting new analysis
- Test retry on failed analysis

## Accessibility Requirements

- **Keyboard Navigation**: All tabs and buttons accessible via keyboard
- **Screen Reader**: Proper ARIA labels on all interactive elements
- **Focus Management**: Focus trapped in dialog, returns to trigger on close
- **Color Contrast**: All badge colors meet WCAG AA standards
- **Loading States**: Announce loading/completion to screen readers

## Performance Considerations

- **Lazy Load Tabs**: Only render active tab content
- **Cache Analysis**: Store fetched analysis in memory, refresh only on demand
- **Skeleton Loaders**: Display immediately, no flash of empty content
- **Optimize Re-renders**: Use computed properties and memoization

## Future Enhancements

- **Export Analysis**: Download as PDF or Markdown
- **Compare Analyses**: View changes between analysis versions
- **Analysis History**: Track and display previous analysis results
- **Inline Editing**: Allow users to annotate or update analysis
- **Share Analysis**: Generate shareable links with read-only access

## References

- shadcn-vue Tabs: https://www.shadcn-vue.com/docs/components/tabs.html
- shadcn-vue Dialog: https://www.shadcn-vue.com/docs/components/dialog.html
- shadcn-vue Alert: https://www.shadcn-vue.com/docs/components/alert.html
- shadcn-vue Badge: https://www.shadcn-vue.com/docs/components/badge.html
- shadcn-vue Card: https://www.shadcn-vue.com/docs/components/card.html
