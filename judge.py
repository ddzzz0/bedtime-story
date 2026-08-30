"""Rubric-based story evaluation: a safety hard gate, a deterministic word-count gate,
and five scored dimensions, plus the logic for picking the best attempt across a run.
"""

import json

import config
import prompts
from llm_client import call_model_json
from schemas import Attempt, DimensionScores, JudgeResult


def compute_overall_pass(scores: DimensionScores, passes_safety: bool, passes_word_count: bool) -> bool:
    # The weakest dimension gates the whole story so one excellent dimension can't
    # paper over one bad one.
    return (
        passes_safety
        and passes_word_count
        and scores.minimum() >= config.MIN_DIMENSION_SCORE_TO_PASS
    )


def judge_story(user_input: str, category: str, story: str) -> JudgeResult:
    # Word count is computed here in plain Python rather than trusted to the LLM's
    # self-report - a simple count is strictly more reliable than asking a model to
    # judge length.
    word_count = len(story.split())
    passes_word_count = config.WORD_COUNT_MIN <= word_count <= config.WORD_COUNT_MAX

    prompt = prompts.build_judge_prompt(user_input, category, story)
    try:
        data = call_model_json(prompt, max_tokens=config.MAX_TOKENS_JUDGE, temperature=config.TEMP_JUDGE)
        raw_scores = data["scores"]
        scores = DimensionScores(
            readability=int(raw_scores["readability"]),
            structure=int(raw_scores["structure"]),
            emotional_arc=int(raw_scores["emotional_arc"]),
            faithfulness=int(raw_scores["faithfulness"]),
            engagement=int(raw_scores["engagement"]),
        )
        passes_safety = bool(data["passes_safety"])
        safety_reason = str(data.get("safety_reason", ""))
        feedback = str(data.get("feedback", ""))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Fail closed: the judge is the last check before content reaches a child, so an
        # unparseable response is treated as a failing/unsafe attempt rather than
        # assumed safe. Deliberately asymmetric with the classifier's fail-open policy.
        scores = DimensionScores(readability=0, structure=0, emotional_arc=0, faithfulness=0, engagement=0)
        passes_safety = False
        safety_reason = "judge_response_unparseable_fail_closed"
        feedback = "The editor's response could not be read; please try again."

    overall_pass = compute_overall_pass(scores, passes_safety, passes_word_count)
    return JudgeResult(
        passes_safety=passes_safety,
        safety_reason=safety_reason,
        scores=scores,
        feedback=feedback,
        word_count=word_count,
        passes_word_count=passes_word_count,
        overall_pass=overall_pass,
    )


def best_safe_attempt(attempts: list[Attempt]) -> Attempt | None:
    safe = [a for a in attempts if a.judge_result.passes_safety]
    if not safe:
        return None  # every attempt was unsafe; caller falls back to the hardcoded story

    def rank(attempt: Attempt) -> tuple:
        scores = attempt.judge_result.scores
        return (scores.minimum(), scores.average(), attempt.judge_result.passes_word_count)

    # Regeneration isn't guaranteed to monotonically improve, so every safe attempt is
    # tracked and the best is chosen at the end rather than trusting the last one.
    return max(safe, key=rank)
