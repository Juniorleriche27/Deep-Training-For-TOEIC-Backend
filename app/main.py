import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_cors_origins, get_settings
from app.dependencies.auth import get_current_profile_id
from app.models import AdherentProfileInitRequest, ChatMessage, ChatMessageRequest, HealthResponse, NotePayload, ScoreCreateRequest, SupportMessageRequest
from app.prompts.coach import build_coach_prompt
from app.rag.knowledge import retrieve_knowledge_context
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
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)


@app.get("/adherent/me")
async def get_me(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_me(profile_id)


@app.post("/adherent/profil/init")
async def init_profile(payload: AdherentProfileInitRequest, profile_id: str = Depends(get_current_profile_id)):
    return repository.init_profile(profile_id, payload.model_dump())


@app.get("/adherent/dashboard")
async def get_dashboard(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_dashboard(profile_id)


@app.get("/adherent/programme")
async def get_programme(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_programme(profile_id)


@app.get("/adherent/scores")
async def get_scores(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_scores(profile_id)


@app.post("/adherent/scores", status_code=201)
async def create_score(payload: ScoreCreateRequest, profile_id: str = Depends(get_current_profile_id)):
    return repository.create_score(profile_id, payload.model_dump())


@app.get("/adherent/notes")
async def get_notes(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_notes(profile_id)


@app.post("/adherent/notes", status_code=201)
async def create_note(payload: NotePayload, profile_id: str = Depends(get_current_profile_id)):
    return repository.create_note(profile_id, payload.model_dump())


@app.put("/adherent/notes/{note_id}")
async def update_note(note_id: str, payload: NotePayload, profile_id: str = Depends(get_current_profile_id)):
    try:
        return repository.update_note(profile_id, note_id, payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/adherent/notes/{note_id}", status_code=204)
async def delete_note(note_id: str, profile_id: str = Depends(get_current_profile_id)):
    try:
        repository.delete_note(profile_id, note_id)
        return None
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/adherent/ressources")
async def get_resources(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_resources(profile_id)


@app.get("/adherent/messages")
async def get_messages(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_messages(profile_id)


@app.post("/adherent/messages", status_code=201)
async def create_support_message(payload: SupportMessageRequest, profile_id: str = Depends(get_current_profile_id)):
    return repository.create_message(profile_id, payload.content)


@app.put("/adherent/messages/{message_id}/read")
async def mark_message_read(message_id: str, profile_id: str = Depends(get_current_profile_id)):
    try:
        return repository.mark_message_read(profile_id, message_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/adherent/coach-ia/context")
async def get_coach_context(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_coach_context(profile_id)


@app.get("/adherent/coach-ia/history")
async def get_chat_history(profile_id: str = Depends(get_current_profile_id)):
    return repository.get_chat_history(profile_id)


@app.post("/adherent/coach-ia/chat", response_model=ChatMessage, status_code=201)
async def create_chat_message(payload: ChatMessageRequest, profile_id: str = Depends(get_current_profile_id)) -> ChatMessage:
    try:
        user_content = payload.content.strip()
        repository.persist_chat_message(profile_id, "user", user_content)

        coach_context = repository.get_coach_context(profile_id)
        knowledge_context = await retrieve_knowledge_context(user_content)
        contextual_message = build_coach_prompt(user_content, coach_context, knowledge_context)

        ai_text = await call_ai_gateway(
            message=contextual_message,
            response_mode=payload.response_mode,
            temperature=payload.temperature,
        )
        assistant_message = repository.persist_chat_message(profile_id, "assistant", ai_text)
    except AIGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatMessage(**assistant_message)
