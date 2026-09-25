"""Minimal HTTP API exposing extract() to the React frontend.

Run: uvicorn api:app --reload --port 8000
"""

import sys,logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent / "anthropic"))
from jobschema import JobPosting  # type: ignore # noqa: E402

from clients import OllamaClient
from extractor import ExtractionFailed, extract # type: ignore

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s | %(message)s",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

client = OllamaClient("llama3.2")


class ExtractRequest(BaseModel):
    text: str


@app.post("/api/extract")
def extract_job(req: ExtractRequest): # type: ignore
    try:
        result = extract(req.text, JobPosting, client) # type: ignore
    except ExtractionFailed as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result.model_dump() # type: ignore
