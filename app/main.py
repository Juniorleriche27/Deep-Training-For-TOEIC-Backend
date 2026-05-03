import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import ChatMessage, ChatMessageRequest, HealthResponse, NotePayload, ScoreCreateRequest, SupportMessageRequest
from app.repositories.adherent_repository import AdherentRepository
from app.services.ai_gateway import AIGatewayError, call_ai_gateway

settings = get_settings()
repository = AdherentRepository()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Deep Training For TOEIC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)


@app.get("/adherent/me")
async def get_me():
    return repository.get_me()


@app.get("/adherent/dashboard")
async def get_dashboard():
    return repository.get_dashboard()


@app.get("/adherent/programme")
async def get_programme():
    return repository.get_programme()


@app.get("/adherent/scores")
async def get_scores():
    return repository.get_scores()


@app.post("/adherent/scores", status_code=201)
async def create_score(payload: ScoreCreateRequest):
    return repository.create_score(payload.model_dump())


@app.get("/adherent/notes")
async def get_notes():
    return repository.get_notes()


@app.post("/adherent/notes", status_code=201)
async def create_note(payload: NotePayload):
    return repository.create_note(payload.model_dump())


@app.put("/adherent/notes/{note_id}")
async def update_note(note_id: str, payload: NotePayload):
    try:
        return repository.update_note(note_id, payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/adherent/notes/{note_id}", status_code=204)
async def delete_note(note_id: str):
    try:
        repository.delete_note(note_id)
        return None
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/adherent/ressources")
async def get_resources():
    return repository.get_resources()


@app.get("/adherent/messages")
async def get_messages():
    return repository.get_messages()


@app.post("/adherent/messages", status_code=201)
async def create_support_message(payload: SupportMessageRequest):
    return repository.create_message(payload.content)


@app.put("/adherent/messages/{message_id}/read")
async def mark_message_read(message_id: str):
    try:
        return repository.mark_message_read(message_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/adherent/coach-ia/context")
async def get_coach_context():
    return repository.get_coach_context()


@app.get("/adherent/coach-ia/history")
async def get_chat_history():
    return repository.get_chat_history()


@app.post("/adherent/coach-ia/chat", response_model=ChatMessage, status_code=201)
async def create_chat_message(payload: ChatMessageRequest) -> ChatMessage:
    try:
        user_message = repository.persist_chat_message("user", payload.content.strip())
        ai_text = await call_ai_gateway(
            message=payload.content.strip(),
            response_mode=payload.response_mode,
            temperature=payload.temperature,
        )
    except AIGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

        assistant_message = repository.persist_chat_message("assistant", ai_text)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatMessage(**assistant_message)
