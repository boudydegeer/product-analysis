# Admin UI - Complete Management System

**Status:** ✅ Implemented and Ready to Use
**Date:** 2026-01-09
**Access:** http://localhost:8892/admin

---

## Overview

We've implemented a complete Admin UI that allows you to manage agents and tools through a web interface. No more Python scripts or SQL commands needed!

## Features Implemented

### 🤖 **Agents Management**
- **View all agents** in a card-based grid layout
- **Create new agents** with complete configuration
- **Edit existing agents** - update any field
- **Delete agents** with confirmation dialog
- **Toggle enabled status** - enable/disable agents with one click

### 🔧 **Tools Management**
- **View all tools** organized by category
- **Create new tools** with Claude SDK-compatible definitions
- **Edit existing tools** - update definition, description, etc.
- **Delete tools** with cascade handling
- **Toggle enabled status** for tools

### 🔗 **Tool Assignments**
- **Assign tools to agents** with custom configuration
- **Configure tool behavior** per agent:
  - Enable/disable for specific agent
  - Set priority order
  - Set usage limits
  - Configure parameter constraints
  - Set approval requirements
- **Remove tool assignments** easily

---

## How to Access

### 1. Start the Backend (if not running)
```bash
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891
```

### 2. Start the Frontend (if not running)
```bash
cd frontend
npm run dev
```

### 3. Navigate to Admin
Open your browser and go to:
```
http://localhost:8892/admin
```

Or click the **"Admin"** link in the sidebar navigation (Settings icon).

---

## User Guide

### Creating a New Agent

1. Go to **Admin** → **Agents** tab
2. Click the **"+ New Agent"** button (floating action button in bottom-right)
3. Fill in the form:

   **Basic Information:**
   - **Name:** Unique identifier (lowercase, no spaces)
     - Example: `code_reviewer`
   - **Display Name:** User-friendly name shown in UI
     - Example: `Rita the Code Reviewer 👩‍💻`
   - **Description:** Short description of the agent's purpose
     - Example: `Expert code reviewer focused on best practices`

   **Appearance:**
   - **Avatar URL:** Emoji or image URL
     - Example: `👩‍💻` or `https://example.com/avatar.png`
   - **Avatar Color:** Hex color for avatar background
     - Example: `#3b82f6` (blue)
   - **Personality Traits:** Tags describing the agent's personality
     - Example: `analytical`, `thorough`, `constructive`

   **Configuration:**
   - **Model:** Claude model to use
     - Options: `claude-sonnet-4-5`, `claude-opus-4-5`, `claude-haiku-4-5`
   - **System Prompt:** Instructions for the agent
     - Example: `You are an expert code reviewer...`
   - **Temperature:** Creativity setting (0.0 - 1.0)
     - 0.2-0.4: Analytical tasks
     - 0.5-0.7: Balanced tasks
     - 0.7-0.9: Creative tasks

   **Advanced:**
   - **Streaming Enabled:** Enable real-time streaming responses
   - **Max Context Tokens:** Maximum context window (default: 200000)
   - **Is Default:** Set as default agent (only one can be default)
   - **Enabled:** Activate the agent immediately

4. Click **"Create Agent"**
5. Success! The agent appears in the list

### Editing an Agent

1. Find the agent in the grid
2. Click the **"Edit"** button
3. Modify any fields
4. Click **"Update Agent"**
5. Changes are applied immediately

### Deleting an Agent

1. Find the agent in the grid
2. Click the **"Delete"** button
3. Confirm in the dialog
4. Agent and all its tool assignments are removed

### Creating a New Tool

1. Go to **Admin** → **Tools** tab
2. Click the **"+ New Tool"** button
3. Fill in the form:

   **Basic Information:**
   - **Name:** Function name (snake_case)
     - Example: `analyze_code`
   - **Description:** What the tool does
     - Example: `Analyzes code for bugs and improvements`
   - **Category:** Tool category for organization
     - Example: `code_quality`
   - **Tool Type:** Source of the tool
     - Options: `builtin`, `custom`, `mcp`

   **Definition (JSON):**
   - Must be valid Claude SDK format
   - Example:
     ```json
     {
       "type": "function",
       "function": {
         "name": "analyze_code",
         "description": "Analyzes code",
         "parameters": {
           "type": "object",
           "properties": {
             "code": {
               "type": "string",
               "description": "Code to analyze"
             },
             "language": {
               "type": "string",
               "enum": ["python", "javascript", "typescript"]
             }
           },
           "required": ["code", "language"]
         }
       }
     }
     ```

   **Configuration:**
   - **Tags:** Keywords for searching (comma-separated)
     - Example: `code`, `analysis`, `quality`
   - **Is Dangerous:** Mark if tool can execute code or modify data
   - **Requires Approval:** Require human approval before use
   - **Example Usage:** Sample invocation (optional)

4. Click **"Create Tool"**
5. Tool is created and ready to assign

### Assigning Tools to Agents

1. Go to **Admin** → **Assignments** tab
2. Select an agent from the dropdown
3. Click **"Assign Tool"** button
4. Select a tool from the list
5. Configure assignment options:
   - **Enabled:** Activate this tool for the agent
   - **Order Index:** Display priority (1 = highest)
   - **Allow Use:** Permission to use (can disable temporarily)
   - **Requires Approval:** Override tool's default approval setting
   - **Usage Limit:** Max uses per session (0 = unlimited)
6. Click **"Assign"**
7. Tool appears in the agent's tools list

### Removing Tool Assignments

1. Go to **Assignments** tab
2. Select the agent
3. Find the tool in the list
4. Click **"Remove"** button
5. Confirm removal
6. Assignment is deleted

---

## API Endpoints Reference

All endpoints are available at `http://localhost:8891/docs`

### Agents
```
POST   /api/v1/admin/agents              Create agent
GET    /api/v1/admin/agents              List all agents
GET    /api/v1/admin/agents/{id}         Get specific agent
PUT    /api/v1/admin/agents/{id}         Update agent
DELETE /api/v1/admin/agents/{id}         Delete agent
```

### Tools
```
POST   /api/v1/admin/tools               Create tool
GET    /api/v1/admin/tools               List all tools
GET    /api/v1/admin/tools/{id}          Get specific tool
PUT    /api/v1/admin/tools/{id}          Update tool
DELETE /api/v1/admin/tools/{id}          Delete tool
```

### Assignments
```
POST   /api/v1/admin/agents/{agent_id}/tools         Assign tool
GET    /api/v1/admin/agents/{agent_id}/tools         List assignments
DELETE /api/v1/admin/agents/{agent_id}/tools/{tool_id}  Remove tool
```

---

## UI Components

### AgentsTable
- **Location:** `frontend/src/components/admin/AgentsTable.vue`
- **Features:** Grid layout, edit/delete actions, status toggle
- **Empty State:** Shows message when no agents exist

### AgentForm
- **Location:** `frontend/src/components/admin/AgentForm.vue`
- **Features:** Dialog-based form, validation, color picker, tag management
- **Modes:** Create (empty form) and Edit (pre-filled)

### ToolsTable
- **Location:** `frontend/src/components/admin/ToolsTable.vue`
- **Features:** Grouped by category, shows type and flags
- **Actions:** Edit, delete, toggle enabled

### ToolForm
- **Location:** `frontend/src/components/admin/ToolForm.vue`
- **Features:** JSON editor with validation, tag management
- **Validation:** Ensures Claude SDK format compliance

### ToolAssignments
- **Location:** `frontend/src/components/admin/ToolAssignments.vue`
- **Features:** Agent selector, tool list, assignment dialog
- **Configuration:** All assignment options exposed

---

## Tips & Best Practices

### Agent Configuration
1. **Use descriptive names:** Make it clear what the agent does
2. **Set appropriate temperature:**
   - Low (0.2-0.4) for analytical tasks
   - Medium (0.5-0.7) for balanced tasks
   - High (0.7-0.9) for creative tasks
3. **Write clear system prompts:** Be specific about the agent's role and behavior
4. **Use personality traits:** Help users understand the agent's approach

### Tool Configuration
1. **Validate JSON definitions:** Use the built-in validator
2. **Provide clear descriptions:** Help Claude understand when to use the tool
3. **Mark dangerous tools:** Set `is_dangerous` for tools that execute code or modify data
4. **Use categories:** Group related tools for better organization
5. **Add tags:** Makes tools searchable and discoverable

### Tool Assignments
1. **Set usage limits:** Prevent abuse of expensive operations
2. **Order matters:** Higher priority tools appear first
3. **Use approval wisely:** Only for truly sensitive operations
4. **Test assignments:** Create a session and verify tools are available

---

## Troubleshooting

### Agent Not Appearing in Selector
**Issue:** Created agent but it doesn't show in the brainstorm agent selector

**Solutions:**
1. Check if agent is **enabled** (toggle in admin UI)
2. Refresh the brainstorm page
3. Clear browser cache
4. Verify agent exists in admin panel

### Tool Not Working
**Issue:** Tool assigned but agent can't use it

**Solutions:**
1. Check if tool assignment is **enabled**
2. Verify `allow_use` is `true`
3. Check tool definition is valid Claude SDK format
4. Look at backend logs for errors

### Form Validation Errors
**Issue:** Can't submit form due to validation

**Solutions:**
1. **Name must be unique:** Change to a different name
2. **Temperature range:** Must be between 0.0 and 1.0
3. **JSON definition:** Must be valid JSON in Claude SDK format
4. **Required fields:** Fill all required fields (marked with *)

### JSON Definition Invalid
**Issue:** Tool definition fails validation

**Solutions:**
1. Use the format from examples in the form
2. Ensure `type: "function"` at root
3. Ensure `function.name` matches tool name
4. Ensure `parameters` has `type: "object"`
5. Check for syntax errors (missing commas, brackets)

---

## Example: Creating a Code Reviewer Agent

Here's a complete example of creating a code review agent:

### Step 1: Create the Agent
```
Name: code_reviewer
Display Name: Rita the Code Reviewer 👩‍💻
Description: Expert code reviewer focused on best practices and security
Avatar URL: 👩‍💻
Avatar Color: #3b82f6
Personality Traits: analytical, thorough, constructive, security-focused
Model: claude-opus-4-5
Temperature: 0.3
System Prompt: You are Rita, an expert code reviewer with 15+ years of experience.
Your role is to review code for bugs, security issues, and improvements...
```

### Step 2: Create a Code Analysis Tool
```json
{
  "type": "function",
  "function": {
    "name": "analyze_code",
    "description": "Analyzes code for bugs, security, and improvements",
    "parameters": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "The code to analyze"
        },
        "language": {
          "type": "string",
          "enum": ["python", "javascript", "typescript", "java"]
        }
      },
      "required": ["code", "language"]
    }
  }
}
```

### Step 3: Assign Tool to Agent
- Select `code_reviewer` agent
- Assign `analyze_code` tool
- Set order_index: 1 (highest priority)
- Enable and allow use

### Step 4: Test
- Go to brainstorm
- Select "Rita the Code Reviewer"
- Ask: "Can you review this Python code?"
- Verify Rita can use the analyze_code tool

---

## Security Considerations

### Admin Access
- Current version has no authentication
- **TODO:** Add admin role/permissions before production
- **Recommendation:** Place behind VPN or auth middleware

### Dangerous Tools
- Mark all code execution tools as `is_dangerous`
- Require approval for sensitive operations
- Audit tool usage via `tool_usage_audit` table

### Tool Definitions
- Validate all JSON definitions
- Sanitize user inputs in tool implementations
- Never trust tool parameters directly

---

## Future Enhancements

### Planned Features
1. **Search & Filtering:** Search agents/tools by name, category, tags
2. **Bulk Operations:** Enable/disable multiple items at once
3. **Import/Export:** Export agent configs as JSON, import from file
4. **Versioning:** Track changes to agents and tools over time
5. **Analytics:** Dashboard showing agent usage, popular tools
6. **Templates:** Pre-built agent templates for common use cases
7. **Tool Marketplace:** Community-contributed tools
8. **Testing:** Test agents directly from admin UI

---

## Support

### Need Help?
- Check [Extension Guide](docs/guides/extending-dynamic-tools.md) for more details
- Check [Usage Guide](docs/guides/dynamic-tools-usage.md) for Python examples
- Check [Executive Summary](EXECUTIVE_SUMMARY.md) for system overview
- Review API docs at http://localhost:8891/docs

### Found a Bug?
Please create an issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots if relevant

---

**Document Version:** 1.0
**Last Updated:** 2026-01-09
**Status:** Production Ready
**Access:** http://localhost:8892/admin
