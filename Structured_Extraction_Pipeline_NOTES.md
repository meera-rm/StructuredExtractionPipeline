# C1: Schema-Validated LLM Extraction — Session Notes

## What C1 is, in one sentence

A function that takes messy text in, returns a validated Python object out,
and never returns garbage — even when the LLM misbehaves. The one new idea
in the whole project: **a validation error is a message you can send back
to the model, not just a crash.**

---

## Concepts, in the order you actually learned them

### 1. Pydantic v2 models
`BaseModel`, type hints (`str`, `int`, `bool`, `list[str]`, `X | None`),
`model_validate()`, `model_validate_json()`. A model is a contract: field
names and types you're willing to accept as correct.

### 2. `ValidationError`
When a dict doesn't match the model, Pydantic raises `ValidationError`
with a structured, machine-readable payload. You inspected it directly:

```json
{
  "type": "int_parsing",
  "loc": ["years_experience_min"],
  "msg": "Input should be a valid integer, unable to parse string as an integer",
  "input": "7+"
}
```

Four parts, each doing a job: `loc` is a *path* (a list, so it can point
into nested models or list items), `type` is machine-branchable, `msg` is
human/LLM-readable, `input` is the offending value echoed back so nothing
is lost.

### 3. `Field(description=...)`
Every description you write gets serialized into JSON Schema and sent to
the model as part of the prompt. **The schema and the prompt are the same
artifact.** You proved this directly: adding descriptions to `title` and
`required_skills` measurably changed real model output — company name
stopped leaking into the title field, "7+ years" started parsing to `7`
instead of `null`.

### 4. The retry loop (the actual lesson)
```
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
```
You wrote `build_prompt`, `build_repair_prompt`, and `extract()` yourself.
The key design point: `original_prompt` is kept separate from the
per-attempt `prompt` so repairs don't nest inside each other — otherwise
attempt 3 would contain three stacked copies of the schema.

### 5. `_strip_fences`
Models wrap JSON in ` ```json ... ``` ` even when told not to. Cheap
string surgery before validation, not part of validation itself.

### 6. `FakeClient`
A test double with the same `complete(prompt) -> str` interface as a real
client, returning pre-scripted responses from a list. This is why
`extract()` never needs to know or care which client it's calling — same
reason you'd inject a connection factory instead of hardcoding a JDBC
string in a Glue job. It made your 8-test suite free and deterministic —
no network, no cost, same result every run.

### 7. Syntax vs. semantics (the interview point)
Constrained/validated output guarantees **shape** — an `int` field will
contain an `int`. It says nothing about whether the value is *correct*.
`remote: bool` can never raise a validation error, yet the model can and
did get it wrong relative to "hybrid, 3 days onsite" in early tests. No
`@field_validator` can catch this generically, because there's no rule
that distinguishes a plausible-but-wrong bool from a correct one.

### 8. Building a labeled eval set
Six `(text, expected_dict)` pairs, two of them real scraped postings.
Per-field exact match for `title`/`company`/`remote`/`years_experience_min`,
a recall-style score for the `required_skills` list (since exact-match on
a list is too strict — order shouldn't matter and one miss shouldn't zero
the whole field). This turned "I found two bugs by eyeballing output" into
"I built infrastructure that finds bugs systematically."

---

## Timeline: what actually happened, and which category each failure belongs to

Two completely different kinds of problem showed up tonight. Separating
them matters, because they teach different things.

### Category A: environment/tooling failures (not about the project)
- Wrong shell, `.venv` not activated → `ModuleNotFoundError`
- Files created via GUI editor silently saved as **0 bytes**, repeatedly
  (`clients.py`, `responses.py`, `test_extractor.py`, `demo.py` all hit
  this at least once) — the editor showed the pasted text but never wrote
  it to disk
- A malformed heredoc left the terminal stuck mid-paste
- API key was valid but the account had no billing credit → `401`

None of these were about Pydantic, LLMs, or retry logic. They were fixed
by working closer to the terminal — `cat > file << 'EOF' ... EOF` writes
directly, no editor save step to fail — and by checking `wc -c` on a file
before assuming its contents matched what you'd just "written."

**The actual skill this taught:** when behavior doesn't match what you
believe you wrote, verify the file on disk before doubting the logic.
That's a real, transferable debugging habit, arguably as valuable as
anything Pydantic-specific.

### Category B: real model-behavior findings (this is the project working)
These only became visible once the tooling was fixed and you could
actually run things.

1. **Description-driven fix:** `required_skills` picked up "production
   pipelines" (a responsibility, not a tech) until the field description
   explicitly excluded responsibilities. Fixed by better prompt/schema
   wording, zero code change to the retry loop.

2. **Input-phrasing-driven bug, same symptom:** AWS was dropped from
   `required_skills` in "Python and Airflow **on** AWS" — 3 for 3,
   reproducibly — and reappeared 3 for 3 after rewriting to "Python,
   Airflow, **and** AWS." Same visible symptom (missing skill) as #1, but
   a completely different root cause: not a schema problem, an *input*
   problem. Nothing in the code changed between these two experiments;
   only the source text did.

3. **Eval-design failure, not extractor failure (St. Xavier posting):**
   `required_skills` scored `0.00` even though the model's answers were
   substantively correct — it extracted `"dea registration in good
   standing"` where the label said `"dea registration"`. Exact-string
   matching after lowercasing is too strict for free-text fields with no
   canonical short form. The eval itself needed fixing, not the model.

4. **Labeling error caught by the eval (ML Engineer posting):**
   `"distributed training"` showed up as "extra" — but it's a real skill
   mentioned in the text; the hand-written label was just incomplete.

5. **A genuine model-capacity boundary (JPMorgan posting):** all 3
   attempts failed identically. Inspecting `e.attempts` showed the model
   wasn't returning a wrong-but-parseable answer — it was echoing back a
   mangled copy of the **JSON Schema itself** (`"properties": {"title":
   ...}`) instead of an instance of it. This is your longest input by far,
   against a 3B local model. Retrying with the same broken output as
   context did not help, because the model hadn't made a fixable mistake —
   it lost track of the task. This is a distinct failure class from
   "wrong type" or "markdown fences": no amount of retrying fixes it,
   because it isn't noise.

---

## What to say in an interview

**"Walk me through the project."**
"It's schema-validated extraction from unstructured text using an LLM. A
Pydantic model defines the target schema; that schema gets serialized into
the prompt via `model_json_schema()`, so the field types and descriptions
I write are literally what the model reads. I call the model, try to
validate the response, and on a `ValidationError` I feed the structured
error — not just 'try again' — back to the model as a follow-up message,
capped at 3 attempts. Every attempt gets logged, so a permanent failure has
a full forensic record instead of a silent drop."

**"What does structured/constrained output actually guarantee?"**
"Shape, not correctness. An `int` field will contain an `int` — it cannot
contain unparseable text. But a `bool` field can contain the wrong boolean
and pass every check I have, because there's no type-level rule that
distinguishes a plausible wrong answer from a correct one. I saw this
directly: 'hybrid, 3 days onsite' is unambiguous to a human, but nothing
in a JSON Schema encodes 'hybrid is not the same as remote.' That's the
line between what validation catches and what it can't."

**"How did you know your extractor was any good, beyond one example
working?"**
"I built a small labeled eval set — six job postings, including two real
scraped ones, with hand-written expected values — and scored per field:
exact match for scalars, a recall-style score for the skills list since
exact match on a list is too strict. That surfaced three different things
at once: a real extraction bug (AWS silently dropped depending on a single
preposition in the source text), a bug in my own eval's scoring logic
(penalizing a correct paraphrase as a total miss), and a genuine capacity
limit of the small local model I was testing against, where a long input
made it lose the task entirely rather than answer it wrong."

**"What would you do differently in production?"**
"Three things. One, separate 'field is unknown' from 'field is
zero/explicitly none' — right now both collapse to `null`, which lost me
a real signal in testing ('no experience required' should mean `0`, not
'unstated'). Two, fuzzy or substring matching for free-text list fields in
the eval, since exact match punishes correct paraphrases. Three, a
length/complexity guard before the call — if a long-context small-model
failure mode returns a schema-echo instead of an answer, I'd rather detect
and short-circuit that (route to a bigger model, or chunk the input) than
retry blindly against a fixed error the model can't actually fix by
retrying."

**"Why not just use Instructor / LangChain's output parser?"**
"Those productionize exactly this pattern, and I'd use one in production.
I built the ~40-line version by hand first specifically so I understood
what the library is doing under the hood — the retry-with-error-as-context
loop, the syntax/semantics gap it can't close, the difference between
native structured-output guarantees and application-level correctness.
Reading Instructor's source *after* writing my own version told me a lot
more than reading it first would have."

---

## Files in this project

| File | Purpose |
|---|---|
| `test_extractor.py` | `JobPosting` schema + 8 tests — the spec `extract()` must satisfy |
| `extractor.py` | `build_prompt`, `build_repair_prompt`, `extract()` — the code you wrote |
| `clients.py` | `FakeClient` (scripted, free, deterministic) and `OllamaClient` (real, local) — same interface, interchangeable |
| `responses.py` | Hand-written bad/good model responses used by the fake client and tests |
| `demo.py` | Runs `extract()` end-to-end with logging, against either client |
| `eval_set.py` | 6 labeled `(text, expected)` examples, 2 of them real scraped postings |
| `eval.py` | Runs the eval set through `extract()`, scores per field, prints a report |
