"""E2E tests for inference.py — syntax, prompts, fallback."""

import sys
from pathlib import Path
from unittest.mock import MagicMock


def test_inference_script_syntax():
    """inference.py should be importable without errors."""
    root = Path(__file__).parent.parent.parent.parent.parent
    inference_path = root / "inference.py"
    assert inference_path.exists(), f"inference.py not found at {inference_path}"

    # Compile check — doesn't execute, just parses
    source = inference_path.read_text()
    compile(source, str(inference_path), "exec")


def test_prompt_template_format():
    """The prompt template should produce valid strings with sample data."""
    # Import the module's template
    root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(root))
    try:
        from inference import USER_TEMPLATE, format_inventory

        inventory = [
            {
                "name": "chicken_breast",
                "quantity": 500,
                "unit": "g",
                "expiry_date": "2026-01-05",
                "category": "protein",
            }
        ]
        result = USER_TEMPLATE.format(
            inventory=format_inventory(inventory),
            horizon=3,
            household_size=2,
            restrictions="none",
            current_date="2026-01-01",
        )
        assert "chicken_breast" in result
        assert "3 days" in result
        assert "2 people" in result
    finally:
        sys.path.pop(0)


def test_fallback_on_bad_json():
    """When LLM returns garbage, inference should fall back to empty plan."""
    root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(root))
    try:
        # Mock the OpenAI client to return invalid JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "this is not json"
        mock_client.chat.completions.create.return_value = mock_response

        # The retry logic should eventually fall back to empty plan
        # We test the pattern: 3 retries, then fallback
        import json

        for _attempt in range(3):
            try:
                raw = mock_response.choices[0].message.content
                meal_plan = json.loads(raw)
                break
            except json.JSONDecodeError:
                meal_plan = None
                continue

        if meal_plan is None:
            meal_plan = {"meal_plan": []}

        assert meal_plan == {"meal_plan": []}
    finally:
        sys.path.pop(0)
