"""Orchestrates classify -> generate -> judge -> revise. Pure logic, no I/O - main.py
is the only place that reads input or prints output.
"""

from collections.abc import Callable

import classifier
import config
import generator
import judge
import prompts
from schemas import Attempt, PipelineResult


def run_pipeline(user_input: str, on_progress: Callable[[str], None] | None = None) -> PipelineResult:
    classification = classifier.classify_and_check_safety(user_input)
    if on_progress:
        on_progress(
            f"classified as '{classification.category}' "
            f"(safe={classification.is_safe}: {classification.reason})"
        )
    if not classification.is_safe:
        return PipelineResult(
            final_story=prompts.SAFETY_REDIRECT_MESSAGE,
            category=classification.category,
            input_blocked=True,
            used_fallback_story=False,
            attempts=[],
        )

    attempts: list[Attempt] = []
    story = generator.generate_story(user_input, classification.category)
    for revision_number in range(config.MAX_REVISIONS + 1):
        result = judge.judge_story(user_input, classification.category, story)
        attempts.append(Attempt(revision_number, story, result))
        if on_progress:
            on_progress(
                f"draft {revision_number}: safety={result.passes_safety} "
                f"weakest={result.scores.minimum()}/5 words={result.word_count}"
            )
        if result.overall_pass or revision_number == config.MAX_REVISIONS:
            break
        if not result.passes_safety:
            story = generator.generate_story_safety_retry(user_input, classification.category)
        else:
            story = generator.revise_story(user_input, classification.category, story, result)

    chosen = judge.best_safe_attempt(attempts)
    if chosen is None:
        if on_progress:
            on_progress("no attempt passed the safety gate; using hardcoded fallback story")
        return PipelineResult(
            final_story=prompts.FALLBACK_STORY,
            category=classification.category,
            input_blocked=False,
            used_fallback_story=True,
            attempts=attempts,
        )
    return PipelineResult(
        final_story=chosen.story_text,
        category=classification.category,
        input_blocked=False,
        used_fallback_story=False,
        attempts=attempts,
    )
