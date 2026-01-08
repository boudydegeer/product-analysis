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
    summary_overview = complexity.get("level")  # Low, Medium, High, Very High
    summary_key_points = (
        [complexity.get("rationale")] if complexity.get("rationale") else []
    )
    summary_metrics = {
        "story_points": complexity.get("story_points"),
        "estimated_hours": complexity.get("estimated_hours"),
        "prerequisite_hours": complexity.get("prerequisite_hours"),
        "total_hours": complexity.get("total_hours"),
    }

    # Extract implementation fields from tasks and affected modules
    primary_areas = [mod["path"] for mod in affected_modules if "path" in mod]
    implementation_architecture = {
        "affected_modules_count": len(affected_modules),
        "primary_areas": primary_areas,
    }

    implementation_technical_details = implementation_tasks

    # Count prerequisites and feature tasks
    prerequisite_count = sum(
        1 for task in implementation_tasks if task.get("task_type") == "prerequisite"
    )
    feature_task_count = sum(
        1 for task in implementation_tasks if task.get("task_type") == "feature"
    )

    implementation_data_flow = {
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
    alternatives = recommendations.get("alternatives", [])
    recommendations_improvements = [alternatives[i] for i in range(len(alternatives))]

    testing_strategy = recommendations.get("testing_strategy")
    recommendations_best_practices = [testing_strategy] if testing_strategy else []

    approach = recommendations.get("approach")
    recommendations_next_steps = [approach] if approach else []

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
