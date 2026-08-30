"""Structured data passed between pipeline stages."""

from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    category: str
    is_safe: bool
    reason: str


@dataclass
class DimensionScores:
    readability: int
    structure: int
    emotional_arc: int
    faithfulness: int
    engagement: int

    def as_dict(self) -> dict[str, int]:
        return {
            "readability": self.readability,
            "structure": self.structure,
            "emotional_arc": self.emotional_arc,
            "faithfulness": self.faithfulness,
            "engagement": self.engagement,
        }

    def minimum(self) -> int:
        return min(self.as_dict().values())

    def average(self) -> float:
        values = list(self.as_dict().values())
        return sum(values) / len(values)

    def weak_dimensions(self, threshold: int) -> list[str]:
        return [name for name, score in self.as_dict().items() if score < threshold]


@dataclass
class JudgeResult:
    passes_safety: bool
    safety_reason: str
    scores: DimensionScores
    feedback: str
    word_count: int
    passes_word_count: bool
    overall_pass: bool


@dataclass
class Attempt:
    revision_number: int  # 0 = initial generation, 1 = first revision, ...
    story_text: str
    judge_result: JudgeResult


@dataclass
class PipelineResult:
    final_story: str
    category: str
    input_blocked: bool  # True: the classifier's input-side gate fired, nothing was generated
    used_fallback_story: bool  # True: every attempt failed safety, hardcoded fallback used
    attempts: list[Attempt] = field(default_factory=list)
