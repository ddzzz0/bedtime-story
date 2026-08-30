# Hippocratic AI Coding Assignment
Welcome to the [Hippocratic AI](https://www.hippocraticai.com) coding assignment

## Instructions
The attached code is a simple python script skeleton. Your goal is to take any simple bedtime story request and use prompting to tell a story appropriate for ages 5 to 10.
- Incorporate a LLM judge to improve the quality of the story
- Provide a block diagram of the system you create that illustrates the flow of the prompts and the interaction between judge, storyteller, user, and any other components you add
- Do not change the openAI model that is being used. 
- Please use your own openAI key, but do not include it in your final submission.
- Otherwise, you may change any code you like or add any files

---

## Rules
- This assignment is open-ended
- You may use any resources you like with the following restrictions
   - They must be resources that would be available to you if you worked here (so no other humans, no closed AIs, no unlicensed code, etc.)
   - Allowed resources include but not limited to Stack overflow, random blogs, chatGPT et al
   - You have to be able to explain how the code works, even if chatGPT wrote it
- DO NOT PUSH THE API KEY TO GITHUB. OpenAI will automatically delete it

---

## What does "tell a story" mean?
It should be appropriate for ages 5-10. Other than that it's up to you. Here are some ideas to help get the brain-juices flowing!
- Use story arcs to tell better stories
- Allow the user to provide feedback or request changes
- Categorize the request and use a tailored generation strategy for each category

---

## How will I be evaluated
Good question. We want to know the following:
- The efficacy of the system you design to create a good story
- Are you comfortable using and writing a python script
- What kinds of prompting strategies and agent design strategies do you use
- Are the stories your tool creates good?
- Can you understand and deconstruct a problem
- Can you operate in an open-ended environment
- Can you surprise us

---

## Other FAQs
- How long should I spend on this? 
No more than 2-3 hours
- Can I change what the input is? 
Sure
- How long should the story be?
You decide

---

# Implementation

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit .env and paste in your own OpenAI key

python3 main.py
```

Set `DEBUG=1` to see the classifier's decision and every draft's judge scores as they happen:

```bash
DEBUG=1 python3 main.py
```

Run the pure-logic smoke tests (no API calls, no key required):

```bash
python3 smoke_test.py
```

## Architecture

Every request passes through four stages: a combined classifier + safety gate, a
category-tailored generator, a rubric-based judge, and a bounded revision loop that feeds
the judge's feedback back into the generator. See system design diagram below. 

<img width="777" height="526" alt="image" src="https://github.com/user-attachments/assets/b5edf8bd-5ba5-41cd-be0c-145891ee418b" />


- **Classifier + Safety Gate** (`classifier.py`) — one LLM call that both picks a category
  (to tailor the generation prompt) and screens the request for anything inappropriate
  *before* any story is written. If flagged, the pipeline stops immediately and returns a
  friendly redirect — no story is ever generated for an unsafe request.
- **Generator** (`generator.py`) — writes the story using a category-specific style guide,
  carrying most of the quality burden itself so the judge loop only has to catch the
  residual misses.
- **Judge** (`judge.py`) — re-checks safety on the *output* (defense in depth — a
  generated story can drift into something inappropriate even from a safe-sounding
  request), checks word count deterministically in Python, and scores five dimensions
  (readability, structure, emotional arc, faithfulness, engagement) from 1-5.
- **Revision loop** (`pipeline.py`) — if the judge fails a draft and revisions remain, it
  either revises in place (quality/length failures — using the previous story plus
  specific feedback) or regenerates from scratch without echoing the failed text (safety
  failures), for up to 2 revisions. Every attempt is tracked and the best *safe* one is
  returned at the end, since revision isn't guaranteed to improve monotonically. If every
  attempt fails the safety gate (should be rare), a hardcoded, pre-vetted fallback story
  is returned instead of ever showing unsafe content.

## Category taxonomy

| Category | Covers | Judge note |
|---|---|---|
| `animal_friendship` | Animals/pets as protagonists or companions | Standard rubric |
| `adventure_exploration` | Journeys, quests, treasure hunts | Looks for a quest → discovery → return arc |
| `fantasy_magic` | Magic, dragons, fairies, enchanted lands | Standard rubric |
| `everyday_life` | Home, school, siblings, small realistic problems | Standard rubric |
| `silly_humor` | Absurd/funny premises, wordplay | Silliness should taper into calm, not peak at the end |
| `calming_nature` | Explicitly sleep-themed, atmospheric (stars, ocean, weather) | Minimal/no conflict is *not* penalized on structure |
| `general` (fallback) | Vague/unclassifiable requests, or classifier failure | Standard rubric |
