"""Tests for analysis mapper utility."""
from app.utils.analysis_mapper import extract_flattened_fields


def test_extract_flattened_fields_complete_workflow():
    """Test extraction with complete workflow structure."""
    result_data = {
        "feature_id": "test-123",
        "complexity": {
            "story_points": 5,
            "estimated_hours": 16,
            "prerequisite_hours": 4,
            "total_hours": 20,
            "level": "High",
            "rationale": "Complex feature requiring multiple components",
        },
        "warnings": [
            {
                "type": "missing_infrastructure",
                "severity": "high",
                "message": "Database models not found",
                "impact": "Must create models first",
            }
        ],
        "repository_state": {
            "has_backend_code": True,
            "has_frontend_code": True,
            "has_database_models": False,
            "has_authentication": True,
            "maturity_level": "partial",
            "notes": "Backend and frontend exist but missing DB models",
        },
        "affected_modules": [
            {
                "path": "/backend/app/models/user.py",
                "change_type": "new",
                "reason": "Create user model",
            },
            {
                "path": "/backend/app/api/users.py",
                "change_type": "modify",
                "reason": "Add user endpoints",
            },
            {
                "path": "/frontend/src/components/UserList.vue",
                "change_type": "new",
                "reason": "User list UI",
            },
        ],
        "implementation_tasks": [
            {
                "id": "task-1",
                "task_type": "prerequisite",
                "description": "Setup database models",
                "estimated_effort_hours": 4,
                "dependencies": [],
                "priority": "high",
            },
            {
                "id": "task-2",
                "task_type": "feature",
                "description": "Implement user management API",
                "estimated_effort_hours": 8,
                "dependencies": ["task-1"],
                "priority": "high",
            },
            {
                "id": "task-3",
                "task_type": "feature",
                "description": "Build user list UI",
                "estimated_effort_hours": 8,
                "dependencies": ["task-2"],
                "priority": "medium",
            },
        ],
        "technical_risks": [
            {
                "category": "security",
                "description": "Password hashing vulnerability",
                "severity": "high",
                "mitigation": "Use bcrypt with salt",
            }
        ],
        "recommendations": {
            "improvements": [
                {
                    "priority": "high",
                    "title": "Add password validation",
                    "description": "Implement strong password requirements",
                    "effort": "2 hours",
                }
            ],
            "alternatives": ["Use OAuth instead"],
            "best_practices": ["Follow OWASP guidelines"],
            "next_steps": ["Setup test environment"],
        },
    }

    # Extract flattened fields
    fields = extract_flattened_fields(result_data)

    # Verify summary fields
    assert fields["summary_overview"] == "Complex feature requiring multiple components"
    assert (
        "Complex feature requiring multiple components" in fields["summary_key_points"]
    )
    assert "⚠️ Database models not found" in fields["summary_key_points"]
    assert (
        "📊 Backend and frontend exist but missing DB models"
        in fields["summary_key_points"]
    )

    # Verify metrics
    assert fields["summary_metrics"]["complexity"] == "high"
    assert "days" in fields["summary_metrics"]["estimated_effort"]
    assert fields["summary_metrics"]["confidence"] == 0.85
    assert fields["summary_metrics"]["story_points"] == 5
    assert fields["summary_metrics"]["estimated_hours"] == 20

    # Verify implementation architecture
    assert "pattern" in fields["implementation_architecture"]
    assert "Full-stack" in fields["implementation_architecture"]["pattern"]
    assert "components" in fields["implementation_architecture"]
    assert len(fields["implementation_architecture"]["components"]) > 0
    assert fields["implementation_architecture"]["affected_modules_count"] == 3
    assert len(fields["implementation_architecture"]["primary_areas"]) == 3

    # Verify technical details
    assert len(fields["implementation_technical_details"]) == 3
    assert fields["implementation_technical_details"][0]["category"] == "task-1"
    assert (
        "database models"
        in fields["implementation_technical_details"][0]["description"].lower()
    )

    # Verify data flow
    assert "description" in fields["implementation_data_flow"]
    assert "steps" in fields["implementation_data_flow"]
    assert fields["implementation_data_flow"]["has_prerequisites"] is True
    assert fields["implementation_data_flow"]["prerequisite_count"] == 1
    assert fields["implementation_data_flow"]["feature_task_count"] == 2
    assert len(fields["implementation_data_flow"]["steps"]) > 0

    # Verify risks
    assert len(fields["risks_technical_risks"]) == 1
    assert fields["risks_technical_risks"][0]["category"] == "security"
    assert len(fields["risks_mitigation_strategies"]) == 1

    # Verify recommendations
    assert len(fields["recommendations_improvements"]) == 1
    assert fields["recommendations_improvements"][0]["priority"] == "high"
    assert (
        fields["recommendations_improvements"][0]["title"] == "Add password validation"
    )
    assert len(fields["recommendations_best_practices"]) == 1
    assert len(fields["recommendations_next_steps"]) == 1


def test_extract_flattened_fields_minimal_workflow():
    """Test extraction with minimal workflow structure."""
    result_data = {
        "complexity": {
            "story_points": 2,
            "estimated_hours": 4,
            "level": "Low",
        },
        "affected_modules": [],
        "implementation_tasks": [],
        "technical_risks": [],
        "recommendations": {},
    }

    fields = extract_flattened_fields(result_data)

    # Should not crash with minimal data
    assert fields["summary_overview"] == ""
    assert fields["summary_key_points"] == []
    assert fields["summary_metrics"]["complexity"] == "low"
    assert fields["summary_metrics"]["estimated_hours"] == 4


def test_extract_flattened_fields_with_old_recommendations_format():
    """Test backward compatibility with old recommendations format."""
    result_data = {
        "complexity": {
            "story_points": 3,
            "estimated_hours": 8,
            "level": "Medium",
        },
        "affected_modules": [],
        "implementation_tasks": [],
        "technical_risks": [],
        "recommendations": {
            "improvements": [
                "Improvement 1: Add caching",
                "Improvement 2: Add monitoring",
            ],
            "alternatives": ["Alternative 1"],
            "testing_strategy": "Unit tests + integration tests",
            "approach": "Iterative development",
        },
    }

    fields = extract_flattened_fields(result_data)

    # Should convert old string format to new object format
    assert len(fields["recommendations_improvements"]) == 2
    assert isinstance(fields["recommendations_improvements"][0], dict)
    assert "title" in fields["recommendations_improvements"][0]
    assert "description" in fields["recommendations_improvements"][0]

    # Should fallback to testing_strategy for best_practices
    assert "Unit tests + integration tests" in fields["recommendations_best_practices"]

    # Should fallback to approach for next_steps
    assert "Iterative development" in fields["recommendations_next_steps"]
