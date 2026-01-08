"""Utility functions for mapping workflow results to flattened Analysis fields.

This module provides functions to extract and transform data from the GitHub
workflow's analysis result structure into the flattened fields of the Analysis model.
"""

from typing import Dict, Any


def extract_flattened_fields(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract flattened fields from workflow result data.

    This function maps the REAL workflow structure to the 13 flattened fields
    in the Analysis model.

    Args:
        result_data: The complete workflow result dictionary

    Returns:
        Dictionary with flattened field names as keys and extracted values
    """
    complexity = result_data.get("complexity") or {}
    implementation_tasks = result_data.get("implementation_tasks") or []
    affected_modules = result_data.get("affected_modules") or []
    technical_risks = result_data.get("technical_risks") or []
    recommendations = result_data.get("recommendations") or {}

    # Extract summary fields from complexity
    summary_overview = complexity.get("rationale", "")  # The descriptive text

    # Build key points from various sources
    summary_key_points = []
    if complexity.get("rationale"):
        summary_key_points.append(complexity.get("rationale"))

    # Add warnings as key points
    warnings = result_data.get("warnings") or []
    for warning in warnings[:3]:  # Limit to top 3 warnings
        if isinstance(warning, dict) and warning.get("message"):
            summary_key_points.append(f"⚠️ {warning['message']}")

    # Add repository state notes if available
    repo_state = result_data.get("repository_state") or {}
    if repo_state.get("notes"):
        summary_key_points.append(f"📊 {repo_state['notes']}")

    # Build metrics in format expected by frontend
    total_hours = complexity.get("total_hours", 0) or complexity.get(
        "estimated_hours", 0
    )
    estimated_days = round(total_hours / 8, 1) if total_hours else 0

    summary_metrics = {
        "complexity": complexity.get("level", "Unknown").lower(),  # low, medium, high
        "estimated_effort": f"{estimated_days} days"
        if estimated_days >= 1
        else f"{total_hours} hours",
        "confidence": 0.85,  # Default confidence, can be enhanced later
        "story_points": complexity.get("story_points"),
        "estimated_hours": total_hours,
    }

    # Extract implementation fields from tasks and affected modules
    primary_areas = [mod["path"] for mod in affected_modules if "path" in mod]

    # Build architecture description
    architecture_pattern = "Modular architecture"  # Default
    if repo_state.get("has_backend_code") and repo_state.get("has_frontend_code"):
        architecture_pattern = "Full-stack architecture (backend + frontend)"
    elif repo_state.get("has_backend_code"):
        architecture_pattern = "Backend-focused architecture"
    elif repo_state.get("has_frontend_code"):
        architecture_pattern = "Frontend-focused architecture"

    # Extract component types from affected modules
    components = set()
    for mod in affected_modules:
        path = mod.get("path", "")
        if "models" in path.lower() or "schema" in path.lower():
            components.add("Data models")
        if (
            "api" in path.lower()
            or "routes" in path.lower()
            or "endpoints" in path.lower()
        ):
            components.add("API endpoints")
        if "services" in path.lower():
            components.add("Business logic services")
        if (
            "components" in path.lower()
            or ".vue" in path
            or ".jsx" in path
            or ".tsx" in path
        ):
            components.add("UI components")
        if "utils" in path.lower() or "helpers" in path.lower():
            components.add("Utility functions")

    implementation_architecture = {
        "affected_modules_count": len(affected_modules),
        "primary_areas": primary_areas,
        "pattern": architecture_pattern,
        "components": list(components),
    }

    # Transform implementation_tasks to match frontend expected structure
    implementation_technical_details = []
    for task in implementation_tasks:
        detail = {
            "category": task.get("id", "Task"),
            "description": task.get("description", ""),
            "estimated_effort": task.get("estimated_effort_hours", 0),
            "priority": task.get("priority", "medium"),
        }
        # Add dependencies as code_locations if available
        if task.get("dependencies"):
            detail["code_locations"] = task["dependencies"]
        implementation_technical_details.append(detail)

    # Count prerequisites and feature tasks
    prerequisite_count = sum(
        1 for task in implementation_tasks if task.get("task_type") == "prerequisite"
    )
    feature_task_count = sum(
        1 for task in implementation_tasks if task.get("task_type") == "feature"
    )

    # Build data flow description and steps
    data_flow_description = ""
    data_flow_steps = []

    if prerequisite_count > 0:
        data_flow_description = f"Implementation requires {prerequisite_count} prerequisite task(s) before {feature_task_count} feature-specific task(s)."
        data_flow_steps.append(
            f"Complete {prerequisite_count} prerequisite tasks (infrastructure, setup)"
        )
        data_flow_steps.append(f"Implement {feature_task_count} feature-specific tasks")
    else:
        data_flow_description = (
            f"Direct implementation with {feature_task_count} task(s)."
        )
        data_flow_steps.append(f"Implement {feature_task_count} tasks")

    # Add affected module information to data flow
    if len(affected_modules) > 0:
        data_flow_steps.append(
            f"Modify {len(affected_modules)} module(s): {', '.join(primary_areas[:3])}"
        )

    implementation_data_flow = {
        "description": data_flow_description,
        "steps": data_flow_steps,
        "has_prerequisites": prerequisite_count > 0,
        "prerequisite_count": prerequisite_count,
        "feature_task_count": feature_task_count,
    }

    # Extract risk fields from technical_risks
    risks_technical_risks = technical_risks

    # Filter risks by category
    risks_security_concerns = [
        risk for risk in technical_risks if risk.get("category") == "security"
    ]

    risks_scalability_issues = [
        risk for risk in technical_risks if risk.get("category") == "scalability"
    ]

    # Extract mitigation strategies from all risks
    risks_mitigation_strategies = [
        risk["mitigation"]
        for risk in technical_risks
        if "mitigation" in risk and risk["mitigation"]
    ]

    # Extract recommendation fields from recommendations
    # Handle both old format (string list) and new format (object list)
    improvements = recommendations.get("improvements", [])
    if improvements:
        # Check if it's the new format (list of objects)
        if isinstance(improvements[0], dict):
            recommendations_improvements = improvements
        else:
            # Old format: convert strings to objects for backward compatibility
            recommendations_improvements = [
                {
                    "priority": "medium",
                    "title": imp[:60] if len(imp) <= 60 else imp[:57] + "...",
                    "description": imp,
                    "effort": None,
                }
                for imp in improvements
            ]
    else:
        # Fallback: use alternatives for backward compatibility
        alternatives = recommendations.get("alternatives", [])
        recommendations_improvements = [
            {
                "priority": "medium",
                "title": alt[:60] if len(alt) <= 60 else alt[:57] + "...",
                "description": alt,
                "effort": None,
            }
            for alt in alternatives
        ]

    # Extract best_practices (new field) or fallback to testing_strategy
    best_practices = recommendations.get("best_practices", [])
    if not best_practices:
        testing_strategy = recommendations.get("testing_strategy")
        best_practices = [testing_strategy] if testing_strategy else []
    recommendations_best_practices = best_practices

    # Extract next_steps (new field) or fallback to approach
    next_steps = recommendations.get("next_steps", [])
    if not next_steps:
        approach = recommendations.get("approach")
        next_steps = [approach] if approach else []
    recommendations_next_steps = next_steps

    return {
        # Summary fields (from complexity)
        "summary_overview": summary_overview,
        "summary_key_points": summary_key_points,
        "summary_metrics": summary_metrics,
        # Implementation fields (from implementation_tasks + affected_modules)
        "implementation_architecture": implementation_architecture,
        "implementation_technical_details": implementation_technical_details,
        "implementation_data_flow": implementation_data_flow,
        # Risk fields (from technical_risks)
        "risks_technical_risks": risks_technical_risks,
        "risks_security_concerns": risks_security_concerns,
        "risks_scalability_issues": risks_scalability_issues,
        "risks_mitigation_strategies": risks_mitigation_strategies,
        # Recommendation fields (from recommendations)
        "recommendations_improvements": recommendations_improvements,
        "recommendations_best_practices": recommendations_best_practices,
        "recommendations_next_steps": recommendations_next_steps,
    }
