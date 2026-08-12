"""Document and text AI translation endpoint using Google Gemini / OpenAI."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter(prefix="/api/translate", tags=["translation"])


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to translate")
    target_language: str = Field(
        ...,
        description="Target language name, e.g., 'Spanish', 'French', 'Hindi', 'German'",
    )


class TranslationResponse(BaseModel):
    translated_text: str
    target_language: str


def _client() -> OpenAI:
    kwargs = {"api_key": settings.openai_api_key}
    if settings.effective_openai_base_url:
        kwargs["base_url"] = settings.effective_openai_base_url
    return OpenAI(**kwargs)


@router.post("", response_model=TranslationResponse)
def translate_text(payload: TranslationRequest) -> TranslationResponse:
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty.",
        )

    system_prompt = (
        f"You are a professional multi-lingual document translator. "
        f"Translate the following text accurately into {payload.target_language}. "
        f"Preserve all Markdown formatting, headings, lists, bullet points, and code blocks."
    )

    try:
        response = _client().chat.completions.create(
            model=settings.openai_chat_model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.text},
            ],
        )
        translated = response.choices[0].message.content or ""
        return TranslationResponse(
            translated_text=translated.strip(),
            target_language=payload.target_language,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {exc}",
        )
