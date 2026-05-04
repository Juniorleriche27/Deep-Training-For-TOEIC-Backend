from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "deeptraining-toeic-api"


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    response_mode: Literal["fast", "normal", "long"] | None = None
    temperature: float = Field(default=0.3, ge=0, le=2)


class ScoreCreateRequest(BaseModel):
    listening: int = Field(ge=0, le=495)
    reading: int = Field(ge=0, le=495)
    format: str = Field(min_length=1, max_length=100)


class NotePayload(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    etape: str | None = Field(default=None, max_length=80)
    content: str | None = None
    words: list[dict] | None = None
    tag: str | None = Field(default=None, max_length=80)


class SupportMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class AdherentProfileInitRequest(BaseModel):
    firstName: str = Field(min_length=1, max_length=120)
    lastName: str = Field(min_length=1, max_length=120)
    currentScore: int = Field(ge=0, le=990)
    targetScore: int = Field(ge=10, le=990)
    toeicDate: str = Field(min_length=10, max_length=10)
    status: Literal["student", "professional", "other"]
    studyLevel: str = Field(min_length=1, max_length=120)
    profession: str = Field(min_length=1, max_length=160)
    mainMotivation: str = Field(min_length=1, max_length=500)


class PublicChatbotRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    page_url: str | None = None
    visitor_context: dict | None = None


class PublicChatbotResponse(BaseModel):
    content: str
    should_book_call: bool
    cta_label: str
    cta_url: str


class ChatMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class CoachContext(BaseModel):
    etape: str
    score: int
    objectif: int
    deadline: str
    weakZones: str


class AdherentUser(BaseModel):
    id: str
    name: str
    avatar: str
    currentStep: int
    currentStepLabel: str
    deadline: str
    profileCompleted: bool | None = None
    onboardingCompleted: bool | None = None
