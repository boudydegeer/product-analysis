# Feature Brief Validation Flow

## Overview

The brainstorming system now includes a complete validation flow for Feature Briefs, allowing PMs to approve, request changes, or discard briefs before creating features in the system.

## User Flow

1. **Brief Generation**: Claude generates a Feature Brief in markdown format with sections:
   - Problem Statement
   - Target Users
   - Core Functionality
   - Success Metrics
   - Technical Considerations

2. **Validation Request**: After presenting the brief, Claude shows three options:
   - ✓ Accept Brief
   - ✎ Request Changes
   - ✕ Discard

3. **Action Paths**:

   **Accept Brief** → Two options:
   - Create Feature in System (parses brief and creates Feature record)
   - Save as Draft (stores in brainstorm metadata)

   **Request Changes** → Claude prompts for specific feedback and iterates

   **Discard** → Claude asks what to explore instead

## Technical Implementation

### Backend Components

**BriefParser Service** (`app/services/brief_parser.py`):
- Parses markdown Feature Briefs into structured `ParsedBrief` dataclass
- Extracts: name, problem statement, target users, functionality, metrics, technical considerations
- Strips markdown formatting from extracted text
- Generates concise description from problem statement

**Interaction Handlers** (`app/api/brainstorms.py`):
- `handle_brief_approval()`: Returns button_group for create/draft options
- `handle_brief_changes_request()`: Prompts PM for specific feedback
- `handle_brief_discard()`: Asks what to explore next
- `handle_feature_creation()`: Parses brief and creates Feature record
- `handle_save_draft()`: Stores brief in brainstorm metadata
- `get_interaction_handler()`: Routes interaction type to handler

**System Prompt Update** (`app/services/brainstorming_service.py`):
- Instructions for presenting Feature Briefs in markdown
- Button group structure for validation options
- Flow diagram for handling each interaction type
- Requirement to always use markdown formatting

### Frontend Components

**TextBlock Markdown Rendering** (`components/brainstorm/blocks/TextBlock.vue`):
- Uses markdown-it with markdown-it-sanitizer
- Renders headings, lists, code blocks, emphasis, links
- Sanitizes dangerous HTML (XSS protection)
- Styled markdown elements for readability

**Smart Link Handling**:
- Internal links (e.g., `/features/123`) use client-side routing
- External links open in new tab with `target="_blank"` and `rel="noopener noreferrer"`
- Click handler for seamless navigation

## Testing

### Unit Tests

- **BriefParser**: 15 tests covering parsing, edge cases, markdown stripping
- **Interaction Handlers**: 8 tests for each handler function and routing
- **TextBlock**: 10 tests for markdown rendering and link handling

### Integration Tests

- Complete validation flow with approval → feature creation
- Request changes flow with iteration
- Discard flow with redirection
- Draft saving in brainstorm metadata
- Parser integration with feature creation

### Coverage

- Backend: 95%+ coverage on new code
- Frontend: 90%+ coverage on TextBlock component

## Usage Example

```typescript
// PM starts brainstorm
await brainstormingService.start("explore-dark-mode")

// Claude generates Feature Brief (markdown)
// PM clicks "Accept Brief"
await handleInteraction({
  type: "approve_brief",
  data: { brief_text: "# Feature Brief: Dark Mode..." }
})

// Claude shows create/draft options
// PM clicks "Create Feature"
await handleInteraction({
  type: "create_feature",
  data: { brief_text: "# Feature Brief: Dark Mode..." }
})

// Feature created, PM gets link: /features/abc-123
```

## Feature Record Structure

When a Feature is created from a brief, it includes:

```json
{
  "id": "uuid",
  "name": "Dark Mode Toggle",
  "description": "Users need the ability to switch between light and dark themes.",
  "status": "pending",
  "priority": 3,
  "metadata": {
    "source": "brainstorm",
    "brainstorm_id": "session-id",
    "brief": {
      "problem_statement": "...",
      "target_users": ["..."],
      "core_functionality": ["..."],
      "success_metrics": ["..."],
      "technical_considerations": ["..."]
    }
  }
}
```

## Future Enhancements

- [ ] Edit brief inline before creating feature
- [ ] Template system for different brief types
- [ ] AI-powered brief quality scoring
- [ ] Export brief to PDF/Markdown file
- [ ] Compare briefs side-by-side
- [ ] Brief versioning and change tracking
