import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.data import ADHERENT_USER, CHAT_HISTORY, COACH_CONTEXT, DASHBOARD_DATA, MESSAGES, NOTES, PROGRAMME, RESOURCES, SCORES
from app.models import ChatMessage, ChatMessageRequest, HealthResponse, NotePayload, ScoreCreateRequest, SupportMessageRequest
from app.services.ai_gateway import AIGatewayError, call_ai_gateway

settings = get_settings()

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
    return ADHERENT_USER


@app.get("/adherent/dashboard")
async def get_dashboard():
    return DASHBOARD_DATA


@app.get("/adherent/programme")
async def get_programme():
    return PROGRAMME


@app.get("/adherent/scores")
async def get_scores():
    return SCORES


@app.post("/adherent/scores", status_code=201)
async def create_score(payload: ScoreCreateRequest):
    for item in SCORES["history"]:
        item["isCurrent"] = False

    row = {
        "date": datetime.now(tz=timezone.utc).date().isoformat(),
        "listening": payload.listening,
        "reading": payload.reading,
        "total": payload.listening + payload.reading,
        "format": payload.format,
        "isCurrent": True,
    }
    SCORES["history"].append(row)
    SCORES["current"] = row["total"]
    SCORES["listening"] = row["listening"]
    SCORES["reading"] = row["reading"]
    DASHBOARD_DATA["score"] = row["total"]
    DASHBOARD_DATA["listening"] = row["listening"]
    DASHBOARD_DATA["reading"] = row["reading"]
    return SCORES


@app.get("/adherent/notes")
async def get_notes():
    return NOTES


@app.post("/adherent/notes", status_code=201)
async def create_note(payload: NotePayload):
    note = {
        "id": f"note-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
        "title": payload.title or "Nouvelle note",
        "meta": f"Mise a jour le {datetime.now(tz=timezone.utc).date().isoformat()}",
        "etape": payload.etape or "",
        "content": payload.content or "",
        "words": payload.words or [],
        "tag": payload.tag,
    }
    NOTES.insert(0, note)
    return note


@app.put("/adherent/notes/{note_id}")
async def update_note(note_id: str, payload: NotePayload):
    for note in NOTES:
        if note["id"] == note_id:
            if payload.title is not None:
                note["title"] = payload.title
            if payload.etape is not None:
                note["etape"] = payload.etape
            if payload.content is not None:
                note["content"] = payload.content
            if payload.words is not None:
                note["words"] = payload.words
            if payload.tag is not None:
                note["tag"] = payload.tag
            note["meta"] = f"Mise a jour le {datetime.now(tz=timezone.utc).date().isoformat()}"
            return note
    raise HTTPException(status_code=404, detail="Note not found")


@app.delete("/adherent/notes/{note_id}", status_code=204)
async def delete_note(note_id: str):
    for index, note in enumerate(NOTES):
        if note["id"] == note_id:
            NOTES.pop(index)
            return None
    raise HTTPException(status_code=404, detail="Note not found")


@app.get("/adherent/ressources")
async def get_resources():
    return RESOURCES


@app.get("/adherent/messages")
async def get_messages():
    return MESSAGES


@app.post("/adherent/messages", status_code=201)
async def create_support_message(payload: SupportMessageRequest):
    message = {
        "id": f"msg-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
        "sender": "Adherent",
        "senderAvatar": ADHERENT_USER.avatar,
        "time": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "content": payload.content,
        "borderColor": "#22d3ff",
    }
    MESSAGES.insert(0, message)
    return message


@app.put("/adherent/messages/{message_id}/read")
async def mark_message_read(message_id: str):
    for message in MESSAGES:
        if message["id"] == message_id:
            message["read"] = True
            return message
    raise HTTPException(status_code=404, detail="Message not found")


@app.get("/adherent/coach-ia/context")
async def get_coach_context():
    return COACH_CONTEXT


@app.get("/adherent/coach-ia/history")
async def get_chat_history():
    return CHAT_HISTORY


@app.post("/adherent/coach-ia/chat", response_model=ChatMessage, status_code=201)
async def create_chat_message(payload: ChatMessageRequest) -> ChatMessage:
    user_message = ChatMessage(
        id=f"user-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
        role="user",
        content=payload.content.strip(),
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )
    CHAT_HISTORY.append(user_message)

    try:
        ai_text = await call_ai_gateway(
            message=payload.content.strip(),
            response_mode=payload.response_mode,
            temperature=payload.temperature,
        )
    except AIGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    assistant_message = ChatMessage(
        id=f"assistant-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
        role="assistant",
        content=ai_text,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )
    CHAT_HISTORY.append(assistant_message)
    return assistant_message
