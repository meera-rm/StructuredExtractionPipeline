"""Run: pytest test_extractor.py -v

These tests are the spec. If they pass, extract() is correct.
They cost nothing -- FakeClient never touches the network.
"""

import pytest
from pydantic import BaseModel, Field, ValidationError # type: ignore

import nonapi.responses as responses
from clients import FakeClient
from extractor import ExtractionFailed, extract # type: ignore


class JobPosting(BaseModel):
    title: str = Field(description="The job title only, e.g. 'Senior Data Engineer'. Do not include the company name.")
    company: str | None = Field(description="Hiring company name, separate from the title.")
    location: str | None
    remote: bool
    years_experience_min: int | None = Field(description="Minimum years of experience required, as a number. Parse it out even if written as '7+ years' or '5-7 yrs'.")
    required_skills: list[str] = Field(description="Concrete technologies only, e.g. 'python', 'airflow'. Do NOT include responsibilities or soft skills like 'production pipelines'.")


TEXT = "Senior Data Engineer at Acme Corp, NYC. 7+ years. Python, Airflow, AWS."


def test_succeeds_first_try():
    """Happy path: no retry needed, client called exactly once."""
    fake = FakeClient([responses.VALID])
    result = extract(TEXT, JobPosting, fake)

    assert isinstance(result, JobPosting)
    assert result.title == "Senior Data Engineer"
    assert result.years_experience_min == 7
    assert len(fake.calls) == 1, "should not retry on success"


def test_strips_markdown_fences():
    """Model wrapped the JSON in ```json fences. Should recover, not crash."""
    fake = FakeClient([responses.FENCED])
    result = extract(TEXT, JobPosting, fake)

    assert result.title == "Senior Data Engineer"
    assert len(fake.calls) == 1, "fence stripping should not need a retry"


def test_retries_on_validation_error():
    """THE CORE TEST. Bad types on attempt 1, valid on attempt 2."""
    fake = FakeClient([responses.WRONG_TYPES, responses.VALID])
    result = extract(TEXT, JobPosting, fake)

    assert result.years_experience_min == 7
    assert result.required_skills == ["Python", "Airflow", "AWS"]
    assert len(fake.calls) == 2, "should have retried exactly once"


def test_error_text_reaches_the_model():
    """The repair prompt must actually contain the validation error.

    Without this assertion you could 'pass' the retry test by just calling
    the model again with the same prompt -- which works by luck, not design.
    """
    fake = FakeClient([responses.WRONG_TYPES, responses.VALID])
    extract(TEXT, JobPosting, fake)

    second_prompt = fake.calls[1]
    assert "int_parsing" in second_prompt or "valid integer" in second_prompt
    assert "7+" in second_prompt, "the offending value should be echoed back"


def test_full_three_attempt_sequence():
    """Fences -> wrong types -> valid. Exercises both error branches."""
    fake = FakeClient([responses.FENCED, responses.WRONG_TYPES, responses.VALID])
    # FENCED parses fine after stripping, so this actually succeeds on try 1.
    result = extract(TEXT, JobPosting, fake)
    assert result.title == "Senior Data Engineer"


def test_prose_then_valid():
    """Model narrated instead of answering. JSONDecodeError branch."""
    fake = FakeClient([responses.PROSE, responses.VALID])
    result = extract(TEXT, JobPosting, fake)

    assert result.title == "Senior Data Engineer"
    assert len(fake.calls) == 2


def test_raises_after_max_attempts():
    """Never gets better. Must raise, must not loop forever."""
    fake = FakeClient([responses.ALWAYS_BAD] * 3)

    with pytest.raises(ExtractionFailed) as exc_info:
        extract(TEXT, JobPosting, fake, max_attempts=3)

    assert len(fake.calls) == 3, "must not exceed max_attempts"
    assert len(exc_info.value.attempts) == 3, "must record every attempt"


def test_respects_max_attempts_setting():
    """max_attempts=2 means 2 calls, not 3."""
    fake = FakeClient([responses.ALWAYS_BAD] * 5)

    with pytest.raises(ExtractionFailed):
        extract(TEXT, JobPosting, fake, max_attempts=2)

    assert len(fake.calls) == 2