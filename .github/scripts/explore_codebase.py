#!/usr/bin/env python3
"""
Codebase Exploration Script using Claude API with tool use.

This script explores a codebase based on a user query, scope, and focus area.
It uses the Anthropic API with tools (read_file, list_directory, search_files)
to let Claude explore the codebase and provide structured findings.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# Configuration
MAX_ITERATIONS = 20
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8192

# Tool definitions for Claude
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file at the specified path. Returns the file content as text. Use this to examine specific files in detail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read, relative to the repository root"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List the contents of a directory. Returns a list of files and subdirectories. Use this to explore the directory structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the directory to list, relative to the repository root. Use '.' for the root directory."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "If true, recursively list all files and directories (up to 3 levels deep). Default is false.",
                    "default": False
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files containing a pattern using grep. Returns matching lines with file paths and line numbers. Use this to find specific code patterns, function definitions, imports, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The search pattern (supports basic regex)"
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in, relative to repository root. Use '.' for root.",
                    "default": "."
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional glob pattern to filter files (e.g., '*.py', '*.ts')",
                    "default": None
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Default is 50.",
                    "default": 50
                }
            },
            "required": ["pattern"]
        }
    }
]


def get_env_var(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Get environment variable with optional default and required check."""
    value = os.environ.get(name, default)
    if required and not value:
        print(f"Error: Required environment variable {name} is not set")
        sys.exit(1)
    return value


def execute_tool(tool_name: str, tool_input: dict, scope: str) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if tool_name == "read_file":
            return execute_read_file(tool_input.get("path", ""), scope)
        elif tool_name == "list_directory":
            return execute_list_directory(
                tool_input.get("path", "."),
                tool_input.get("recursive", False),
                scope
            )
        elif tool_name == "search_files":
            return execute_search_files(
                tool_input.get("pattern", ""),
                tool_input.get("path", "."),
                tool_input.get("file_pattern"),
                tool_input.get("max_results", 50),
                scope
            )
        else:
            return f"Error: Unknown tool '{tool_name}'"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"


def check_scope(path: str, scope: str) -> bool:
    """Check if a path is within the allowed scope."""
    if scope == "full":
        return True

    # Normalize path
    normalized = path.lstrip("./")

    if scope == "backend":
        return normalized.startswith("backend") or normalized == "backend"
    elif scope == "frontend":
        return normalized.startswith("frontend") or normalized == "frontend"

    return True


def execute_read_file(path: str, scope: str) -> str:
    """Read a file and return its contents."""
    if not check_scope(path, scope):
        return f"Error: Path '{path}' is outside the allowed scope '{scope}'. Only paths within /{scope} are accessible."

    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File '{path}' does not exist"
        if not file_path.is_file():
            return f"Error: '{path}' is not a file"

        # Limit file size to prevent reading huge files
        max_size = 100 * 1024  # 100KB
        if file_path.stat().st_size > max_size:
            return f"Error: File '{path}' is too large (>{max_size} bytes). Try reading specific sections or use search_files to find relevant parts."

        content = file_path.read_text(encoding="utf-8", errors="replace")
        return content
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


def execute_list_directory(path: str, recursive: bool, scope: str) -> str:
    """List directory contents."""
    # Determine the base path based on scope
    if scope == "backend" and path == ".":
        path = "backend"
    elif scope == "frontend" and path == ".":
        path = "frontend"
    elif not check_scope(path, scope):
        return f"Error: Path '{path}' is outside the allowed scope '{scope}'. Only paths within /{scope} are accessible."

    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"
        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"

        entries = []
        if recursive:
            # Recursive listing with depth limit
            for item in sorted(dir_path.rglob("*")):
                # Limit depth to 3 levels
                relative = item.relative_to(dir_path)
                if len(relative.parts) <= 3:
                    entry_type = "dir" if item.is_dir() else "file"
                    entries.append(f"{entry_type}: {item}")
        else:
            for item in sorted(dir_path.iterdir()):
                entry_type = "dir" if item.is_dir() else "file"
                entries.append(f"{entry_type}: {item}")

        if not entries:
            return f"Directory '{path}' is empty"

        return "\n".join(entries[:200])  # Limit to 200 entries
    except Exception as e:
        return f"Error listing directory '{path}': {str(e)}"


def execute_search_files(pattern: str, path: str, file_pattern: str | None, max_results: int, scope: str) -> str:
    """Search for pattern in files using grep."""
    # Determine the base path based on scope
    if scope == "backend" and path == ".":
        path = "backend"
    elif scope == "frontend" and path == ".":
        path = "frontend"
    elif not check_scope(path, scope):
        return f"Error: Path '{path}' is outside the allowed scope '{scope}'. Only paths within /{scope} are accessible."

    try:
        search_path = Path(path)
        if not search_path.exists():
            return f"Error: Search path '{path}' does not exist"

        # Build grep command
        cmd = ["grep", "-rn", "--include=*"]

        if file_pattern:
            cmd = ["grep", "-rn", f"--include={file_pattern}"]

        cmd.extend([pattern, str(search_path)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout
        if not output:
            return f"No matches found for pattern '{pattern}' in '{path}'"

        # Limit results
        lines = output.strip().split("\n")
        if len(lines) > max_results:
            lines = lines[:max_results]
            lines.append(f"\n... (truncated, showing first {max_results} of {len(output.strip().split(chr(10)))} results)")

        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return f"Error: Search timed out after 30 seconds"
    except Exception as e:
        return f"Error searching files: {str(e)}"


def build_system_prompt(scope: str, focus: str) -> str:
    """Build the system prompt based on scope and focus."""
    scope_instruction = ""
    if scope == "backend":
        scope_instruction = """
SCOPE RESTRICTION: You are ONLY allowed to explore the /backend directory.
Do not attempt to access files outside of /backend.
When listing the root directory, start with 'backend' instead of '.'."""
    elif scope == "frontend":
        scope_instruction = """
SCOPE RESTRICTION: You are ONLY allowed to explore the /frontend directory.
Do not attempt to access files outside of /frontend.
When listing the root directory, start with 'frontend' instead of '.'."""
    else:
        scope_instruction = """
SCOPE: You have access to the full codebase (both backend and frontend)."""

    focus_instructions = {
        "patterns": """
FOCUS: Coding Patterns
- Identify recurring code patterns and conventions used in the codebase
- Look for design patterns (Factory, Singleton, Repository, etc.)
- Note naming conventions for files, classes, functions, variables
- Find common utilities and helper functions
- Identify error handling patterns
- Look for testing patterns and conventions""",
        "files": """
FOCUS: Relevant Files
- Find files most relevant to the user's query
- Identify entry points and main modules
- Locate configuration files
- Find related test files
- Identify files that would need modification for related features""",
        "architecture": """
FOCUS: System Architecture
- Understand the overall system design and structure
- Identify the main components and their responsibilities
- Map out data flow and communication patterns
- Find API endpoints and their handlers
- Identify database models and relationships
- Look for service boundaries and integrations""",
        "dependencies": """
FOCUS: Dependencies
- Identify external libraries and frameworks used
- Find configuration for package managers (package.json, pyproject.toml, etc.)
- Look for API integrations with external services
- Identify database and storage dependencies
- Find infrastructure dependencies (Docker, CI/CD, etc.)"""
    }

    focus_instruction = focus_instructions.get(focus, focus_instructions["patterns"])

    return f"""You are a senior software architect exploring a codebase to answer questions and provide insights.

{scope_instruction}

{focus_instruction}

EXPLORATION GUIDELINES:
1. Start by understanding the directory structure
2. Read key files to understand the codebase organization
3. Use search_files to find specific patterns, functions, or imports
4. Be thorough but efficient - don't read every file, focus on what's relevant
5. When you have enough information, provide your findings

IMPORTANT:
- Be concise but thorough in your exploration
- Focus on answering the user's specific query
- Provide actionable insights and specific file references
- Include relevant code snippets when helpful
- If you can't find something, say so rather than guessing

When you're done exploring and ready to provide your findings, compile them into a structured response.
Your final response should be a comprehensive answer to the user's query based on what you discovered."""


def build_user_prompt(query: str, scope: str, focus: str) -> str:
    """Build the user prompt for the exploration."""
    return f"""Please explore this codebase to answer the following question:

**Query:** {query}

**Scope:** {scope} ({"full codebase" if scope == "full" else f"only /{scope} directory"})
**Focus:** {focus}

Start by exploring the relevant directory structure, then dive into specific files to understand the codebase and answer my question.

When you're done, provide your findings in a structured format including:
1. A summary of your findings
2. Relevant files you discovered
3. Key patterns or architecture notes (based on focus area)
4. Code examples if applicable
5. Recommendations or insights

Begin your exploration now."""


def run_exploration(
    client: anthropic.Anthropic,
    query: str,
    scope: str,
    focus: str,
    exploration_id: str
) -> dict[str, Any]:
    """Run the exploration loop with Claude."""
    system_prompt = build_system_prompt(scope, focus)
    user_prompt = build_user_prompt(query, scope, focus)

    messages = [{"role": "user", "content": user_prompt}]

    total_input_tokens = 0
    total_output_tokens = 0
    tool_calls_made = 0
    iteration = 0

    print(f"Starting exploration with query: {query}")
    print(f"Scope: {scope}, Focus: {focus}")
    print("-" * 50)

    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n[Iteration {iteration}/{MAX_ITERATIONS}]")

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Check if Claude wants to use tools or is done
        if response.stop_reason == "end_turn":
            # Claude is done - extract final response
            print("\nClaude completed exploration")
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            return build_result(
                exploration_id=exploration_id,
                query=query,
                scope=scope,
                focus=focus,
                status="completed",
                final_response=final_text,
                tokens={
                    "input": total_input_tokens,
                    "output": total_output_tokens,
                    "total": total_input_tokens + total_output_tokens
                },
                tool_calls_made=tool_calls_made
            )

        elif response.stop_reason == "tool_use":
            # Process tool calls
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_calls_made += 1
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    print(f"  Tool: {tool_name}")
                    if tool_name == "read_file":
                        print(f"    Path: {tool_input.get('path', 'N/A')}")
                    elif tool_name == "list_directory":
                        print(f"    Path: {tool_input.get('path', '.')}, Recursive: {tool_input.get('recursive', False)}")
                    elif tool_name == "search_files":
                        print(f"    Pattern: {tool_input.get('pattern', 'N/A')}")

                    result = execute_tool(tool_name, tool_input, scope)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop reason
            print(f"Unexpected stop reason: {response.stop_reason}")
            break

    # Reached max iterations
    print(f"\nReached maximum iterations ({MAX_ITERATIONS})")
    return build_result(
        exploration_id=exploration_id,
        query=query,
        scope=scope,
        focus=focus,
        status="completed",
        final_response="Exploration reached maximum iterations. Partial results may be available in the conversation.",
        tokens={
            "input": total_input_tokens,
            "output": total_output_tokens,
            "total": total_input_tokens + total_output_tokens
        },
        tool_calls_made=tool_calls_made,
        warning="Reached maximum iteration limit"
    )


def build_result(
    exploration_id: str,
    query: str,
    scope: str,
    focus: str,
    status: str,
    final_response: str,
    tokens: dict[str, int],
    tool_calls_made: int,
    warning: str | None = None
) -> dict[str, Any]:
    """Build the structured result from exploration."""
    # Try to parse structured data from the response
    results = parse_exploration_response(final_response)

    result = {
        "exploration_id": exploration_id,
        "query": query,
        "scope": scope,
        "focus": focus,
        "status": status,
        "results": results,
        "metadata": {
            "model": MODEL,
            "tokens_used": tokens,
            "tool_calls_made": tool_calls_made,
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    }

    if warning:
        result["warning"] = warning

    return result


def parse_exploration_response(response: str) -> dict[str, Any]:
    """Parse the exploration response into structured data."""
    # Default structure
    results = {
        "summary": "",
        "relevant_files": [],
        "key_patterns": [],
        "code_examples": [],
        "architecture_notes": "",
        "dependencies": [],
        "recommendations": [],
        "confidence": "medium",
        "raw_response": response
    }

    # Extract summary (first paragraph or text before first heading)
    lines = response.split("\n")
    summary_lines = []
    for line in lines:
        if line.startswith("#") or line.startswith("**"):
            break
        if line.strip():
            summary_lines.append(line.strip())

    if summary_lines:
        results["summary"] = " ".join(summary_lines[:3])
    else:
        # Use first non-empty line
        for line in lines:
            if line.strip():
                results["summary"] = line.strip()[:500]
                break

    # Extract file paths mentioned (simple heuristic)
    import re
    file_patterns = re.findall(r'[`\'"]?([a-zA-Z0-9_\-./]+\.(py|ts|tsx|js|jsx|vue|json|yaml|yml|md|toml))[`\'"]?', response)
    results["relevant_files"] = list(set(f[0] for f in file_patterns))[:20]

    # Extract patterns mentioned
    pattern_keywords = ["pattern", "convention", "approach", "structure", "design"]
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in pattern_keywords):
            if line.strip().startswith("-") or line.strip().startswith("*"):
                pattern = line.strip().lstrip("-*").strip()
                if pattern and len(pattern) < 200:
                    results["key_patterns"].append(pattern)

    results["key_patterns"] = results["key_patterns"][:10]

    # Determine confidence based on response length and specificity
    if len(response) > 2000 and len(results["relevant_files"]) > 5:
        results["confidence"] = "high"
    elif len(response) < 500 or "could not find" in response.lower() or "no matches" in response.lower():
        results["confidence"] = "low"

    return results


def write_error_result(
    exploration_id: str,
    query: str,
    scope: str,
    focus: str,
    error: str
) -> dict[str, Any]:
    """Create an error result structure."""
    return {
        "exploration_id": exploration_id,
        "query": query,
        "scope": scope,
        "focus": focus,
        "status": "failed",
        "error": error,
        "results": {
            "summary": f"Exploration failed: {error}",
            "relevant_files": [],
            "key_patterns": [],
            "code_examples": [],
            "architecture_notes": "",
            "dependencies": [],
            "recommendations": [],
            "confidence": "low"
        },
        "metadata": {
            "model": MODEL,
            "tokens_used": {"input": 0, "output": 0, "total": 0},
            "tool_calls_made": 0,
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    }


def main():
    """Main entry point for the exploration script."""
    # Read environment variables
    api_key = get_env_var("ANTHROPIC_API_KEY", required=True)
    exploration_id = get_env_var("EXPLORATION_ID", default="unknown")
    query = get_env_var("QUERY", default="")
    scope = get_env_var("SCOPE", default="full")
    focus = get_env_var("FOCUS", default="patterns")

    output_file = "/tmp/exploration_result.json"

    # Validate inputs
    if not query:
        print("Error: QUERY environment variable is required")
        result = write_error_result(
            exploration_id=exploration_id,
            query=query,
            scope=scope,
            focus=focus,
            error="QUERY environment variable is required"
        )
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    # Validate scope
    if scope not in ["full", "backend", "frontend"]:
        print(f"Warning: Invalid scope '{scope}', defaulting to 'full'")
        scope = "full"

    # Validate focus
    if focus not in ["patterns", "files", "architecture", "dependencies"]:
        print(f"Warning: Invalid focus '{focus}', defaulting to 'patterns'")
        focus = "patterns"

    print(f"Exploration Configuration:")
    print(f"  ID: {exploration_id}")
    print(f"  Query: {query}")
    print(f"  Scope: {scope}")
    print(f"  Focus: {focus}")
    print()

    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Run exploration
        result = run_exploration(
            client=client,
            query=query,
            scope=scope,
            focus=focus,
            exploration_id=exploration_id
        )

        # Write result to file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n{'=' * 50}")
        print(f"Exploration complete!")
        print(f"Status: {result['status']}")
        print(f"Tokens used: {result['metadata']['tokens_used']['total']}")
        print(f"Tool calls: {result['metadata']['tool_calls_made']}")
        print(f"Results saved to: {output_file}")

        # Print summary
        if result["results"].get("summary"):
            print(f"\nSummary: {result['results']['summary'][:200]}...")

    except anthropic.APIError as e:
        print(f"Anthropic API error: {e}")
        result = write_error_result(
            exploration_id=exploration_id,
            query=query,
            scope=scope,
            focus=focus,
            error=f"Anthropic API error: {str(e)}"
        )
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

        result = write_error_result(
            exploration_id=exploration_id,
            query=query,
            scope=scope,
            focus=focus,
            error=f"Unexpected error: {str(e)}"
        )
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        sys.exit(1)


if __name__ == "__main__":
    main()
