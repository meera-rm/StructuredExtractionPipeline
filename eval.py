"""Run: python eval.py

Runs every (text, expected) pair in eval_set.py through extract() and
scores the result field by field. This is the difference between
"I found two bugs by hand" and "I built a way to systematically find bugs."
"""

from __future__ import annotations

from eval_set import EXAMPLES
from clients import OllamaClient
from extractor import ExtractionFailed, extract
from test_extractor import JobPosting

EXACT_FIELDS = ["title", "company", "remote", "years_experience_min"]


def score_skills(actual: list[str], expected: list[str]) -> tuple[float, set, set]:
    """Recall-style score for a list field: what fraction of expected
    items actually showed up. Order doesn't matter, one miss doesn't
    zero out the whole field.

    Returns (score 0..1, missing items, extra items) so a report can
    show not just the number but WHAT went wrong.
    """
    actual_set = set(a.lower().strip() for a in actual)
    expected_set = set(e.lower().strip() for e in expected)

    if not expected_set:
        # nothing was supposed to be found; perfect score iff nothing was
        return (1.0 if not actual_set else 0.0), set(), actual_set

    matched = actual_set & expected_set
    missing = expected_set - actual_set
    extra = actual_set - expected_set
    return len(matched) / len(expected_set), missing, extra


def run_eval(client) -> None:
    field_hits = {f: 0 for f in EXACT_FIELDS}
    field_total = {f: 0 for f in EXACT_FIELDS}
    skill_scores = []
    failures = []

    for i, (text, expected) in enumerate(EXAMPLES, start=1):
        print(f"\n{'=' * 60}")
        print(f"Example {i}/{len(EXAMPLES)}")
        print("=" * 60)

        try:
            result = extract(text, JobPosting, client)
        except ExtractionFailed as e:
            print(f"  EXTRACTION FAILED after {len(e.attempts)} attempts")
            for a in e.attempts:
                print(f"    attempt {a['attempt']}: {str(a.get('error',''))[:200]}")
            failures.append(i)
            continue

        result_dict = result.model_dump()

        for field in EXACT_FIELDS:
            field_total[field] += 1
            actual_val = result_dict.get(field)
            expected_val = expected.get(field)
            ok = actual_val == expected_val
            field_hits[field] += int(ok)
            mark = "OK" if ok else "MISS"
            print(f"  [{mark:4}] {field:22} actual={actual_val!r:30} expected={expected_val!r}")

        score, missing, extra = score_skills(
            result_dict.get("required_skills", []), expected.get("required_skills", [])
        )
        skill_scores.append(score)
        mark = "OK" if score == 1.0 else "PART" if score > 0 else "MISS"
        print(f"  [{mark:4}] required_skills        score={score:.2f}")
        if missing:
            print(f"         missing: {sorted(missing)}")
        if extra:
            print(f"         extra:   {sorted(extra)}")

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    for field in EXACT_FIELDS:
        hits, total = field_hits[field], field_total[field]
        pct = 100 * hits / total if total else 0
        print(f"  {field:22} {hits}/{total}  ({pct:.0f}%)")

    if skill_scores:
        avg = sum(skill_scores) / len(skill_scores)
        print(f"  {'required_skills (avg)':22} {avg:.2f}")

    if failures:
        print(f"\n  Extraction raised ExtractionFailed on examples: {failures}")


if __name__ == "__main__":
    run_eval(OllamaClient("llama3.2"))