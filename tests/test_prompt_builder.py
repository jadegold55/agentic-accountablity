import importlib
from pathlib import Path
import sys


def load_prompt_builder_module():
    summary_path = Path(__file__).resolve().parents[1] / "lambda" / "summary_agent"
    sys.path.insert(0, str(summary_path))
    importlib.invalidate_caches()
    return importlib.import_module("prompt_builder")


def test_build_summary_prompt_includes_completion_notes() -> None:
    prompt_builder = load_prompt_builder_module()

    prompt = prompt_builder.build_summary_prompt(
        {
            "per_task": {"Code sesh": 4.0},
            "per_day": {"Monday": 4.0},
            "completion_notes": [
                {
                    "event_title": "Code sesh",
                    "completion_summary": "Finished most of the implementation.",
                }
            ],
        }
    )

    assert "Completion notes from replies:" in prompt
    assert "Code sesh: Finished most of the implementation." in prompt
    assert (
        "Write a brief weekly summary for the human based on these results." in prompt
    )
    assert "Do not mention internal tools, charts, or implementation details." in prompt
