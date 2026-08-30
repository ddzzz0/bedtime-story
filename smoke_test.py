"""Plain-assert sanity checks for the pure decision logic in judge.py - no API calls.

Run with: python3 smoke_test.py
"""

import config
from judge import best_safe_attempt, compute_overall_pass
from schemas import Attempt, DimensionScores, JudgeResult


def make_result(
    readability=5, structure=5, emotional_arc=5, faithfulness=5, engagement=5,
    passes_safety=True, word_count=500,
) -> JudgeResult:
    scores = DimensionScores(readability, structure, emotional_arc, faithfulness, engagement)
    passes_word_count = config.WORD_COUNT_MIN <= word_count <= config.WORD_COUNT_MAX
    return JudgeResult(
        passes_safety=passes_safety,
        safety_reason="",
        scores=scores,
        feedback="",
        word_count=word_count,
        passes_word_count=passes_word_count,
        overall_pass=compute_overall_pass(scores, passes_safety, passes_word_count),
    )


def test_all_high_scores_pass():
    assert make_result().overall_pass is True


def test_one_weak_dimension_fails():
    assert make_result(structure=3).overall_pass is False


def test_good_scores_but_bad_length_fails():
    assert make_result(word_count=100).overall_pass is False


def test_unsafe_fails_regardless_of_scores():
    assert make_result(passes_safety=False).overall_pass is False


def test_best_safe_attempt_empty_list_returns_none():
    assert best_safe_attempt([]) is None


def test_best_safe_attempt_all_unsafe_returns_none():
    attempts = [Attempt(0, "story", make_result(passes_safety=False))]
    assert best_safe_attempt(attempts) is None


def test_best_safe_attempt_picks_highest_weakest_dimension():
    weak = Attempt(0, "weak story", make_result(structure=3))
    strong = Attempt(1, "strong story", make_result(structure=5))
    assert best_safe_attempt([weak, strong]) is strong


def test_best_safe_attempt_ignores_unsafe_even_if_higher_scoring():
    unsafe_but_high = Attempt(0, "unsafe", make_result(passes_safety=False))
    safe_but_lower = Attempt(1, "safe", make_result(structure=4))
    assert best_safe_attempt([unsafe_but_high, safe_but_lower]) is safe_but_lower


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} smoke tests passed")
