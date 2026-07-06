"""Manual extraction endpoint — for testing the NLP pipeline without Slack."""
from fastapi import APIRouter
from pydantic import BaseModel

from services.nlp import ProjectExtraction, extract_from_message

router = APIRouter()


class ExtractRequest(BaseModel):
    text: str


@router.post("/extract", response_model=ProjectExtraction, tags=["NLP"])
def extract(body: ExtractRequest) -> ProjectExtraction:
    """Extract structured project fields from a raw text string.

    Useful for testing the NLP pipeline without a live Slack connection.
    """
    return extract_from_message(body.text)
