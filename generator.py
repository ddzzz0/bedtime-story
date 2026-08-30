"""Story generation and revision. All three functions return plain story text."""

import config
import prompts
from llm_client import call_model
from schemas import JudgeResult


def generate_story(user_input: str, category: str) -> str:
    return call_model(
        prompts.build_generator_prompt(user_input, category),
        max_tokens=config.MAX_TOKENS_STORY,
        temperature=config.TEMP_GENERATE,
    ).strip()


def revise_story(
    user_input: str, category: str, previous_story: str, judge_result: JudgeResult
) -> str:
    return call_model(
        prompts.build_revision_prompt(user_input, category, previous_story, judge_result),
        max_tokens=config.MAX_TOKENS_STORY,
        temperature=config.TEMP_REVISE,
    ).strip()


def generate_story_safety_retry(user_input: str, category: str) -> str:
    # A fresh draw from the original prompt plus an extra caution note - deliberately
    # does NOT echo the previous (unsafe) story back into the model.
    return call_model(
        prompts.build_safety_retry_prompt(user_input, category),
        max_tokens=config.MAX_TOKENS_STORY,
        temperature=config.TEMP_GENERATE,
    ).strip()
