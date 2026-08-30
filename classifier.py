"""Input-side classification and safety gate: one combined LLM call that both tailors
the generation strategy and stops obviously unsafe requests before any story is written.
"""

import json

import config
import prompts
from llm_client import call_model_json
from schemas import ClassificationResult


def classify_and_check_safety(user_input: str) -> ClassificationResult:
    try:
        data = call_model_json(
            prompts.build_classifier_prompt(user_input),
            max_tokens=config.MAX_TOKENS_CLASSIFIER,
            temperature=config.TEMP_CLASSIFIER,
        )
        category = data["category"]
        if category not in config.CATEGORIES and category != config.DEFAULT_CATEGORY:
            category = config.DEFAULT_CATEGORY
        return ClassificationResult(
            category=category,
            is_safe=bool(data["is_safe"]),
            reason=str(data.get("reason", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Fail open: low stakes since the judge's output-side safety gate (judge.py) is
        # the real backstop. Rejecting a legitimate request over a classifier hiccup
        # would be worse than proceeding with a generic category.
        return ClassificationResult(
            category=config.DEFAULT_CATEGORY,
            is_safe=True,
            reason="classification_failed_fail_open",
        )
