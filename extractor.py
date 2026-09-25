"""THE ONE FILE YOU WRITE. Everything else is scaffolding.

    text -> prompt(schema) -> LLM -> raw string
                                       |
                            json.loads + model_validate
                                       |
                  +--------------------+-------------------+
              valid                                  ValidationError
                |                                          |
            return obj                  append error text -> retry (max 3)
                                                           |
                                                exhausted -> log + raise

Run `pytest test_extractor.py` to check your work. Six tests. Make them pass.
"""

from __future__ import annotations

import json
import logging
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

log = logging.getLogger("extractor")

T = TypeVar("T", bound=BaseModel)


class ExtractionFailed(Exception):
    """Raised when all attempts are exhausted.

    Carries `attempts` -- a list of dicts, one per try, each with at least
    {"attempt": int, "raw_response": str, "error": ...}. This is your DLQ
    record. Without it you cannot debug a failure in production.
    """

    def __init__(self, message: str, attempts: list[dict]): # type: ignore
        super().__init__(message)
        self.attempts = attempts # type: ignore


def build_prompt(text: str, model_cls: Type[T]) -> str:
    """Turn the schema + input text into the first prompt.

    TODO(you):
      1. schema = model_cls.model_json_schema()
      2. Return a string containing the schema (json.dumps it, indent=2)
         and the input text, clearly delimited.
      3. Tell the model: ONLY raw JSON, no fences, no commentary.

    Try printing model_json_schema() once on its own. Everything you typed
    in jobschema.py shows up in there -- that's the bridge between your
    Python class and the model.
    """
    schema = model_cls.model_json_schema()
    field_names = list(schema["properties"].keys())
    skeleton = json.dumps({name: "..." for name in field_names}, indent=2)
    field_rules = "\n".join(
        f"    - {name}: {info['description']}"
        for name, info in schema["properties"].items()
        if "description" in info
    )
    return f"""Extract data matching this JSON Schema:


        {json.dumps(schema, indent=2)}

        Return ONLY the JSON object. No markdown fences, no commentary.
        Return a single flat JSON object with exactly these top-level keys: {field_names}
        Do NOT return the schema itself. Do NOT wrap the answer in "properties", "type", or any other schema keyword.
        For any field typed as a number: if the text gives a range (e.g. "$180,000-280,000/year"),
        use the lower bound as a plain integer with no currency symbols, commas, or units (e.g. 180000).

        Field-specific rules (read carefully, each field is distinct even if related):
{field_rules}

        Your answer must look like this shape (values replaced with the real extracted data):

        {skeleton}

        --- TEXT ---
        {text}
        --- END ---"""


def build_repair_prompt(original_prompt: str, bad_response: str, error_text: str) -> str:
    """Build the follow-up prompt after a failure.

    TODO(you): include the original request, what the model returned, and
    the error. Ask for the corrected COMPLETE object -- not a diff, not just
    the broken field. Partial repairs are a whole class of bug you don't
    want to debug.

    This function is the entire lesson of C1. A validation error is not a
    crash; it's a message you can send back.
    """
    return f"""{original_prompt}

    --- YOUR PREVIOUS RESPONSE ---
    {bad_response}
    --- END ---

    That response failed validation with these errors:

    {error_text}

    Fix ONLY these problems. Return the corrected, COMPLETE JSON object.
    Do not return a diff or a partial object."""

    raise NotImplementedError

def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]      # drop the ```json line
        s = s.rsplit("```", 1)[0]     # drop the closing fence
    return s.strip()

def extract(
    text: str,
    model_cls: Type[T],
    client, # type: ignore
    max_attempts: int = 3,
) -> T:
    """Extract a validated `model_cls` from `text`. Never returns garbage.

    TODO(you):

      prompt = build_prompt(...)
      attempts = []

      for attempt in 1..max_attempts:
          raw = client.complete(prompt)

          try:
              obj = model_validate_json(model_cls, raw)
          except ValidationError as e:
              # e.json(indent=2) is the repair instruction
              # record it, build a repair prompt, continue
          except (json.JSONDecodeError, ValueError) as e:
              # not even JSON -- different message, same strategy
              # record it, build a repair prompt, continue

          # success: log which attempt won, return obj

      raise ExtractionFailed(..., attempts)

    Things the tests check that are easy to miss:
      - strip markdown fences before parsing (```json ... ```)
      - append to `attempts` on EVERY iteration, success included
      - the error text must appear in the next prompt
      - never call the client more than max_attempts times
    """
  
    # prompt = build_prompt(text, model_cls)
    # raw = client.complete(prompt)
    # return model_cls.model_validate_json(raw)
    # raise NotImplementedError

#def extract(text, model_cls, client, max_attempts=3):
    original_prompt = build_prompt(text, model_cls)
    prompt = original_prompt
    attempts = []

    for attempt in range(1, max_attempts + 1):
        raw = client.complete(prompt) # type: ignore
        record = {"attempt": attempt, "raw_response": raw} # type: ignore

        try:
            obj = model_cls.model_validate_json(_strip_fences(raw)) # type: ignore
        except ValidationError as e:
            error_text = e.json(indent=2)
            record["error"] = error_text
            attempts.append(record) # type: ignore
            log.info(attempt);
            log.warning("validation_failed attempt=%s error=%s", attempt, error_text)
            prompt = build_repair_prompt(original_prompt, raw, error_text) # type: ignore
            continue
        except ValueError as e:
            error_text = f"That was not valid JSON: {e}"
            record["error"] = error_text
            attempts.append(record) # type: ignore
            log.warning("json_decode_failed attempt=%s error=%s", attempt, error_text)
            prompt = build_repair_prompt(original_prompt, raw, error_text) # type: ignore
            continue

        record["status"] = "ok"
        attempts.append(record) # type: ignore
        log.info("succeeded attempt=%s", attempt)
        return obj

    raise ExtractionFailed(
        f"Failed to extract {model_cls.__name__} after {max_attempts} attempts",
        attempts,
    )
    