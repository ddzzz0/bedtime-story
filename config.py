"""Constants shared across the pipeline. Nothing here calls the network."""

# Assignment constraint: do not change the model. Hardcoded (not env-driven) so it's
# visually obvious to a reader that it can't be swapped via configuration.
MODEL_NAME = "gpt-3.5-turbo"

# Token budgets. A single user request can trigger up to ~7 LLM calls (1 classify +
# up to 3 generate + up to 3 judge), so these are sized per-call rather than reusing
# the skeleton's flat max_tokens=3000 for everything.
MAX_TOKENS_CLASSIFIER = 150
MAX_TOKENS_JUDGE = 400
MAX_TOKENS_STORY = 1200

# Temperatures: deterministic for classify/judge, creative for a first draft, a bit
# more contained for revisions so they stay close edits rather than a fresh draw.
TEMP_CLASSIFIER = 0.0
TEMP_JUDGE = 0.0
TEMP_GENERATE = 0.9
TEMP_REVISE = 0.65

MAX_REVISIONS = 2  # up to 3 total generation attempts (1 initial + 2 revisions)

SCORE_MIN = 1
SCORE_MAX = 5
MIN_DIMENSION_SCORE_TO_PASS = 4  # weakest rubric dimension must be >= this to pass

# ~350-800 words is roughly a 2.5-6 minute read-aloud at a natural bedtime-story pace.
# (350, not 400: gpt-3.5-turbo follows length instructions loosely, and 340-400 word
# outputs read as complete, well-paced stories in practice - see README limitations.)
WORD_COUNT_MIN = 350
WORD_COUNT_MAX = 800

API_MAX_RETRIES = 1  # handed to the OpenAI client's own retry/backoff handling

CATEGORIES = [
    "animal_friendship",
    "adventure_exploration",
    "fantasy_magic",
    "everyday_life",
    "silly_humor",
    "calming_nature",
]
DEFAULT_CATEGORY = "general"
