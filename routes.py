from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ai_core.gemini_generator import (
    GeminiConfigError,
    GeminiDocumentGenerator,
    GeminiGenerationError,
)

router = APIRouter()
gemini_generator = GeminiDocumentGenerator()


class DocumentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    document_type: str = Field(..., min_length=2, max_length=200)
    parties: str = Field(..., min_length=2, max_length=5000)
    terms: str = Field(..., min_length=2, max_length=10000)
    dates: str = Field("", max_length=200)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        response = gemini_generator.generate_document(
            request.document_type,
            request.parties,
            request.terms,
            request.dates,
        )
    except GeminiConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except GeminiGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"document": response}
