import logging

import responses
from clients import FakeClient, OllamaClient
from extractor import ExtractionFailed, extract
from test_extractor import JobPosting

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s | %(message)s",
)

TEXT = """
Senior Data Engineer - Acme Corp
New York, NY (hybrid, 3 days onsite)

We're hiring a Senior Data Engineer with 7+ years building
production pipelines. You'll work in Python, Airflow, and AWS.
Base salary 145,000 - 175,000 depending on experience.
"""

#CLIENT = FakeClient([responses.FENCED, responses.WRONG_TYPES, responses.VALID])
CLIENT = OllamaClient("llama3.2")
if __name__ == "__main__":
    try:
        result = extract(TEXT, JobPosting, CLIENT)
        print("\n=== EXTRACTED ===")
        print(result.model_dump_json(indent=2))
    except ExtractionFailed as e:
        print("\n=== FAILED, all attempts ===")
        for a in e.attempts:
            print(f"\n--- attempt {a['attempt']} ---")
            print(a.get("raw_response", "")[:300])
            print("ERROR:", str(a.get("error", ""))[:300])
