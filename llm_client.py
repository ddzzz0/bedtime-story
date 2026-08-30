"""Thin wrapper around the OpenAI SDK. Every call in this project goes through here so
the model name, retry policy, and error handling only live in one place.
"""

import json
import os
import re

from openai import AuthenticationError, BadRequestError, OpenAI, OpenAIError

import config


class LLMCallError(RuntimeError):
    """The API key is missing/invalid, or a call failed even after the SDK's own retries."""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMCallError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        # max_retries handles transient network/429/5xx errors with backoff; auth and
        # bad-request errors are never retried by the SDK since retrying can't fix those.
        _client = OpenAI(api_key=api_key, max_retries=config.API_MAX_RETRIES)
    return _client


def _create_completion(client: OpenAI, *, json_mode: bool, **kwargs):
    if json_mode:
        try:
            return client.chat.completions.create(
                response_format={"type": "json_object"}, **kwargs
            )
        except BadRequestError:
            pass  # this model snapshot may not support JSON mode; the prompt itself
            # already asks for JSON-only output, so a plain call still works.
    return client.chat.completions.create(**kwargs)


def _call(prompt: str, *, system: str | None, max_tokens: int, temperature: float, json_mode: bool) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    kwargs = dict(
        model=config.MODEL_NAME,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=False,
    )
    try:
        resp = _create_completion(get_client(), json_mode=json_mode, **kwargs)
        return resp.choices[0].message.content or ""
    except AuthenticationError as e:
        raise LLMCallError(f"OpenAI rejected the API key: {e}") from e
    except BadRequestError as e:
        raise LLMCallError(f"OpenAI rejected the request: {e}") from e
    except OpenAIError as e:  # rate limits/connection/server errors, after SDK retries
        raise LLMCallError(f"OpenAI API call failed: {e}") from e


def call_model(prompt: str, *, system: str | None = None, max_tokens: int, temperature: float) -> str:
    return _call(prompt, system=system, max_tokens=max_tokens, temperature=temperature, json_mode=False)


def call_model_json(prompt: str, *, system: str | None = None, max_tokens: int, temperature: float) -> dict:
    text = _call(prompt, system=system, max_tokens=max_tokens, temperature=temperature, json_mode=True)
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: the model sometimes wraps JSON in prose or a markdown fence even when
    # asked not to. Grab the first {...} span and try again before giving up.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))  # let a genuine parse failure raise here
    raise json.JSONDecodeError("No JSON object found in model response", text, 0)
