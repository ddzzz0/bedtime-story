import os
import sys

from dotenv import load_dotenv

import pipeline
from llm_client import LLMCallError

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

1, build a small offline eval set to catch regressions systematically 
2, add OpenAI's Moderation API as an additional, non-prompted safety layer 
3, build the feedback loop the README suggests (letting a user ask for changes to a story they already received)
"""


def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    debug = os.getenv("DEBUG") == "1"

    def on_progress(message: str) -> None:
        if debug:
            print(f"[debug] {message}", file=sys.stderr)

    user_input = input("What kind of story do you want to hear? ")

    try:
        result = pipeline.run_pipeline(user_input, on_progress=on_progress)
    except LLMCallError as e:
        print(f"Sorry, something went wrong talking to the story service: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print(result.final_story)


if __name__ == "__main__":
    main()
