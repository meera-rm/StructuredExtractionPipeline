import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from jobschema import JobPosting

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

TEXT = """
Senior Data Engineer - Acme Corp
New York, NY (hybrid, 3 days onsite)

We're hiring a Senior Data Engineer with 7+ years building
production pipelines. You'll work in Python and Airflow on AWS.
Base salary 145,000 - 175,000 depending on experience.
"""

schema = JobPosting.model_json_schema()

prompt = (
    f"Extract data matching this JSON Schema:\n\n{json.dumps(schema, indent=2)}\n\n"
    f"Return ONLY the JSON object, no markdown fences, no commentary.\n\n"
    f"Return a single flat JSON object with exactly these top-level keys and their values — do NOT return the schema itself, do NOT wrap the answer in properties"
    f"--- TEXT ---\n{TEXT}\n--- END ---"
)

resp = client.messages.create(# type: ignore
    model="claude-sonnet-4-5",
    max_tokens=1500,
    temperature=0,
    messages=[{"role": "user", "content": prompt}],
) # type: ignore

raw = resp.content[0].text# type: ignore
print("RAW RESPONSE:")
print(raw)# type: ignore
print("-" * 40)

obj = JobPosting.model_validate_json(raw)# type: ignore
print("PARSED:")
print(obj)