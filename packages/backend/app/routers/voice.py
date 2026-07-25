"""voice.py — Tier 2 voice logging endpoints.

Thin router: validate, call voice_service. Mutating, so guarded by require_api_key
(open when API_KEY is unset in dev, same as the rest of the app).
"""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.voice import VoiceBatchRequest, VoiceLogRequest
from app.security import require_api_key
from app.services import voice_service

router = APIRouter(prefix="/api/voice", tags=["voice"], dependencies=[Depends(require_api_key)])


@router.post("/log")
def voice_log(body: VoiceLogRequest, conn=Depends(get_conn)):
    return voice_service.log_transcript(conn, body.transcript)


@router.post("/batch")
def voice_batch(body: VoiceBatchRequest, conn=Depends(get_conn)):
    return voice_service.log_batch(conn, body.entries)
