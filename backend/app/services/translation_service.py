"""
Telugu ↔ English Translation Service.
Uses NVIDIA NIM for accurate formal government document translation.
"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.copilot import Translation
from app.models.user import User
from app.schemas.copilot import TranslateRequest, TranslateResponse, TranslationHistoryItem
from app.utils.gemini_client import generate_text, TRANSLATION_PROMPT

SUPPORTED_LANGUAGES = {"Telugu", "English"}
MAX_CHARS = 10_000


class TranslationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def translate(self, request: TranslateRequest, user: User) -> TranslateResponse:
        if request.source_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported source language: {request.source_language}")
        if request.target_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported target language: {request.target_language}")
        if request.source_language == request.target_language:
            raise HTTPException(status_code=400, detail="Source and target language must be different")
        if len(request.text) > MAX_CHARS:
            raise HTTPException(status_code=400, detail=f"Text exceeds {MAX_CHARS} character limit")

        prompt = TRANSLATION_PROMPT.format(
            source_language=request.source_language,
            target_language=request.target_language,
            text=request.text,
        )
        translated = await generate_text(prompt)
        word_count = len(request.text.split())

        record = Translation(
            user_id=user.id,
            source_language=request.source_language,
            target_language=request.target_language,
            source_text=request.text,
            translated_text=translated,
            word_count=word_count,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return TranslateResponse(
            id=record.id,
            source_language=record.source_language,
            target_language=record.target_language,
            source_text=record.source_text,
            translated_text=record.translated_text,
            word_count=word_count,
            created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20) -> list[TranslationHistoryItem]:
        result = await self.db.execute(
            select(Translation)
            .where(Translation.user_id == user.id)
            .order_by(desc(Translation.created_at))
            .limit(limit)
        )
        return [
            TranslationHistoryItem(
                id=r.id,
                source_language=r.source_language,
                target_language=r.target_language,
                preview=r.source_text[:80] + ("…" if len(r.source_text) > 80 else ""),
                word_count=r.word_count,
                created_at=str(r.created_at),
            )
            for r in result.scalars().all()
        ]
