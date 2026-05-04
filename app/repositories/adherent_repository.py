import logging
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.data import ADHERENT_USER, CHAT_HISTORY, COACH_CONTEXT, DASHBOARD_DATA, MESSAGES, NOTES, PROGRAMME, RESOURCES, SCORES
from app.services.supabase_client import SupabaseNotConfiguredError, get_app_schema_client

logger = logging.getLogger("deeptraining.adherent_repository")


class AdherentRepository:
    def __init__(self) -> None:
        self.settings = get_settings()

    def get_me(self, profile_id: str) -> dict[str, Any]:
        def operation():
            row = (
                get_app_schema_client()
                .from_("profiles")
                .select("id, full_name, avatar, current_step, current_step_label, deadline_label, toeic_date, profile_completed, onboarding_completed")
                .eq("id", profile_id)
                .limit(1)
                .execute()
            )
            data = self._single(row.data, "profile")
            return {
                "id": data["id"],
                "name": data["full_name"],
                "avatar": data["avatar"],
                "currentStep": data["current_step"],
                "currentStepLabel": data["current_step_label"],
                "deadline": self._resolve_deadline_label(data.get("toeic_date"), data["deadline_label"]),
                "profileCompleted": bool(data.get("profile_completed")),
                "onboardingCompleted": bool(data.get("onboarding_completed")),
            }

        return self._with_fallback(
            "get_me",
            operation,
            {
                **ADHERENT_USER.model_dump(),
                "profileCompleted": False,
                "onboardingCompleted": False,
            },
        )

    def init_profile(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def operation():
            schema = get_app_schema_client()
            full_name = f"{payload['firstName'].strip()} {payload['lastName'].strip()}".strip()
            listening_score, reading_score = self._split_total_score(payload["currentScore"])

            updated = (
                schema.from_("profiles")
                .update(
                    {
                        "first_name": payload["firstName"].strip(),
                        "last_name": payload["lastName"].strip(),
                        "full_name": full_name,
                        "target_score": payload["targetScore"],
                        "toeic_date": payload["toeicDate"],
                        "deadline_label": self._deadline_label_from_date(payload["toeicDate"]),
                        "status": payload["status"],
                        "study_level": payload["studyLevel"].strip(),
                        "profession": payload["profession"].strip(),
                        "main_motivation": payload["mainMotivation"].strip(),
                        "profile_completed": True,
                        "onboarding_completed": True,
                        "start_score": payload["currentScore"],
                        "current_score": payload["currentScore"],
                        "listening_score": listening_score,
                        "reading_score": reading_score,
                    }
                )
                .eq("id", profile_id)
                .execute()
            )
            self._single(updated.data, "profile")

            current_rows = (
                schema.from_("score_entries")
                .select("id")
                .eq("profile_id", profile_id)
                .eq("is_current", True)
                .limit(1)
                .execute()
            ).data or []
            schema.from_("score_entries").update({"is_current": False}).eq("profile_id", profile_id).execute()
            initial_score_payload = {
                "profile_id": profile_id,
                "taken_on": datetime.now(tz=timezone.utc).date().isoformat(),
                "listening": listening_score,
                "reading": reading_score,
                "format_label": "Initial",
                "is_current": True,
            }
            if current_rows:
                schema.from_("score_entries").update(initial_score_payload).eq("id", current_rows[0]["id"]).execute()
            else:
                schema.from_("score_entries").insert(initial_score_payload).execute()

            return {
                "profile": self.get_me(profile_id),
                "dashboard": self.get_dashboard(profile_id),
                "coachContext": self.get_coach_context(profile_id),
            }

        return self._with_fallback_write(
            "init_profile",
            operation,
            {
                "profile": {
                    **self.get_me(profile_id),
                    "name": f"{payload['firstName'].strip()} {payload['lastName'].strip()}".strip(),
                    "profileCompleted": True,
                    "onboardingCompleted": True,
                },
                "dashboard": self._fallback_dashboard_after_init(payload),
                "coachContext": self._fallback_coach_context_after_init(payload),
            },
        )

    def get_dashboard(self, profile_id: str) -> dict[str, Any]:
        def operation():
            view_row = (
                get_app_schema_client()
                .from_("v_adherent_dashboard")
                .select("*")
                .eq("profile_id", profile_id)
                .limit(1)
                .execute()
            )
            dashboard = self._single(view_row.data, "dashboard")

            missions = (
                get_app_schema_client()
                .from_("daily_missions")
                .select("mission_number, title, subtitle, priority")
                .eq("profile_id", profile_id)
                .order("sort_order")
                .execute()
            ).data or []

            progression = (
                get_app_schema_client()
                .from_("program_steps")
                .select("step_number, name, status_label, progress_percent")
                .order("step_number")
                .execute()
            ).data or []

            activity = (
                get_app_schema_client()
                .from_("activity_entries")
                .select("happened_at, action_label, type_label")
                .eq("profile_id", profile_id)
                .order("happened_at", desc=True)
                .limit(10)
                .execute()
            ).data or []

            progression_percent = self._compute_progression_percent(progression)
            return {
                "score": dashboard["current_score"],
                "scoreStart": dashboard["start_score"],
                "scoreObjectif": dashboard["target_score"],
                "listening": dashboard["listening_score"],
                "reading": dashboard["reading_score"],
                "regularite": dashboard["regularity_percent"],
                "regulariteLabel": dashboard["regularity_label"],
                "risquePrincipal": dashboard["risk_primary"],
                "risqueDetail": dashboard["risk_detail"],
                "missionDuJour": [
                    {
                        "num": item["mission_number"],
                        "title": item["title"],
                        "sub": item["subtitle"],
                        "priority": item["priority"],
                    }
                    for item in missions
                ],
                "progression": [
                    {
                        "num": item["step_number"],
                        "name": item["name"],
                        "status": item["status_label"],
                        **({"percent": item["progress_percent"]} if item["progress_percent"] is not None else {}),
                    }
                    for item in progression
                ],
                "progressionPercent": progression_percent,
                "recentActivity": [
                    {
                        "date": self._format_timestamp(item["happened_at"]),
                        "action": item["action_label"],
                        "type": item["type_label"],
                    }
                    for item in activity
                ],
                "coachTip": dashboard["coach_tip"],
            }

        return self._with_fallback("get_dashboard", operation, DASHBOARD_DATA)

    def get_programme(self, profile_id: str) -> list[dict[str, Any]]:
        def operation():
            steps = (
                get_app_schema_client()
                .from_("program_steps")
                .select("id, step_number, name, description, status_label, status_tone, progress_percent, progress_detail, is_active, is_locked")
                .order("step_number")
                .execute()
            ).data or []
            items = (
                get_app_schema_client()
                .from_("program_step_items")
                .select("step_id, label, color, sort_order")
                .order("sort_order")
                .execute()
            ).data or []
            by_step: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                by_step.setdefault(item["step_id"], []).append({"label": item["label"], "color": item["color"]})

            return [
                {
                    "num": str(step["step_number"]),
                    "name": step["name"],
                    "status": step["status_label"],
                    "statusTone": step["status_tone"],
                    "desc": step["description"],
                    "items": by_step.get(step["id"], []),
                    **({"progress": f'{step["progress_percent"]}%'} if step["progress_percent"] is not None else {}),
                    **({"progressDetail": step["progress_detail"]} if step["progress_detail"] else {}),
                    **({"active": True} if step["is_active"] else {}),
                    **({"locked": True} if step["is_locked"] else {}),
                }
                for step in steps
            ]

        return self._with_fallback("get_programme", operation, PROGRAMME)

    def get_scores(self, profile_id: str) -> dict[str, Any]:
        def operation():
            profile = (
                get_app_schema_client()
                .from_("profiles")
                .select("current_score, start_score, listening_score, reading_score, target_score, coach_tip")
                .eq("id", profile_id)
                .limit(1)
                .execute()
            )
            profile_data = self._single(profile.data, "profile scores")

            history = (
                get_app_schema_client()
                .from_("score_entries")
                .select("taken_on, listening, reading, total, format_label, is_current")
                .eq("profile_id", profile_id)
                .order("taken_on")
                .execute()
            ).data or []
            analysis = (
                get_app_schema_client()
                .from_("score_analysis")
                .select("part_label, percent, level_label")
                .eq("profile_id", profile_id)
                .order("part_label")
                .execute()
            ).data or []

            history_start = history[0] if history else None
            return {
                "current": profile_data["current_score"],
                "currentStart": profile_data["start_score"],
                "listening": profile_data["listening_score"],
                "listeningStart": history_start["listening"] if history_start else profile_data["listening_score"],
                "reading": profile_data["reading_score"],
                "readingStart": history_start["reading"] if history_start else profile_data["reading_score"],
                "objectif": profile_data["target_score"],
                "history": [
                    {
                        "date": item["taken_on"],
                        "listening": item["listening"],
                        "reading": item["reading"],
                        "total": item["total"],
                        "format": item["format_label"],
                        **({"isCurrent": True} if item["is_current"] else {}),
                    }
                    for item in history
                ],
                "analysis": [
                    {
                        "part": item["part_label"],
                        "percent": item["percent"],
                        "level": item["level_label"],
                    }
                    for item in analysis
                ],
                "coachTip": profile_data["coach_tip"],
            }

        return self._with_fallback("get_scores", operation, SCORES)

    def create_score(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def operation():
            schema = get_app_schema_client()
            schema.from_("score_entries").update({"is_current": False}).eq("profile_id", profile_id).execute()
            inserted = (
                schema.from_("score_entries")
                .insert(
                    {
                        "profile_id": profile_id,
                        "taken_on": datetime.now(tz=timezone.utc).date().isoformat(),
                        "listening": payload["listening"],
                        "reading": payload["reading"],
                        "format_label": payload["format"],
                        "is_current": True,
                    }
                )
                .execute()
            )
            row = self._single(inserted.data, "score entry")
            schema.from_("profiles").update(
                {
                    "current_score": row["total"],
                    "listening_score": row["listening"],
                    "reading_score": row["reading"],
                }
            ).eq("id", profile_id).execute()
            schema.from_("activity_entries").insert(
                {
                    "profile_id": profile_id,
                    "action_label": "Nouveau score ajoute",
                    "type_label": "Score",
                }
            ).execute()
            return self.get_scores(profile_id)

        return self._with_fallback_write("create_score", operation, self._fallback_create_score(payload))

    def get_notes(self, profile_id: str) -> list[dict[str, Any]]:
        def operation():
            notes = (
                get_app_schema_client()
                .from_("notes")
                .select("id, title, meta, step_label, content, tag, created_at, updated_at")
                .eq("profile_id", profile_id)
                .order("updated_at", desc=True)
                .execute()
            ).data or []
            words = (
                get_app_schema_client()
                .from_("note_words")
                .select("note_id, word, state")
                .order("created_at")
                .execute()
            ).data or []
            by_note: dict[str, list[dict[str, Any]]] = {}
            for item in words:
                by_note.setdefault(item["note_id"], []).append({"word": item["word"], "state": item["state"]})
            return [
                {
                    "id": note["id"],
                    "title": note["title"],
                    "meta": note["meta"] or self._note_meta(note["updated_at"]),
                    "etape": note["step_label"],
                    "content": note["content"],
                    "words": by_note.get(note["id"], []),
                    **({"tag": note["tag"]} if note["tag"] else {}),
                }
                for note in notes
            ]

        return self._with_fallback("get_notes", operation, NOTES)

    def create_note(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def operation():
            schema = get_app_schema_client()
            inserted = (
                schema.from_("notes")
                .insert(
                    {
                        "profile_id": profile_id,
                        "title": payload.get("title") or "Nouvelle note",
                        "meta": self._note_meta(),
                        "step_label": payload.get("etape") or "",
                        "content": payload.get("content") or "",
                        "tag": payload.get("tag"),
                    }
                )
                .execute()
            )
            note = self._single(inserted.data, "note")
            words = payload.get("words") or []
            if words:
                schema.from_("note_words").insert(
                    [{"note_id": note["id"], "word": item["word"], "state": item.get("state", "")} for item in words]
                ).execute()
            return self._map_note(note, words)

        return self._with_fallback_write("create_note", operation, self._fallback_create_note(payload))

    def update_note(self, profile_id: str, note_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def operation():
            schema = get_app_schema_client()
            update_payload: dict[str, Any] = {
                "meta": self._note_meta(),
            }
            if payload.get("title") is not None:
                update_payload["title"] = payload["title"]
            if payload.get("etape") is not None:
                update_payload["step_label"] = payload["etape"]
            if payload.get("content") is not None:
                update_payload["content"] = payload["content"]
            if "tag" in payload:
                update_payload["tag"] = payload.get("tag")
            updated = (
                schema.from_("notes")
                .update(update_payload)
                .eq("id", note_id)
                .eq("profile_id", profile_id)
                .execute()
            )
            note = self._single(updated.data, "note")
            if payload.get("words") is not None:
                schema.from_("note_words").delete().eq("note_id", note_id).execute()
                if payload["words"]:
                    schema.from_("note_words").insert(
                        [{"note_id": note_id, "word": item["word"], "state": item.get("state", "")} for item in payload["words"]]
                    ).execute()
            words = payload.get("words")
            if words is None:
                words = (
                    schema.from_("note_words").select("word, state").eq("note_id", note_id).order("created_at").execute()
                ).data or []
            return self._map_note(note, words)

        fallback = self._fallback_update_note(note_id, payload)
        return self._with_fallback_write("update_note", operation, fallback, not_found_message="Note not found")

    def delete_note(self, profile_id: str, note_id: str) -> bool:
        def operation():
            deleted = (
                get_app_schema_client()
                .from_("notes")
                .delete()
                .eq("id", note_id)
                .eq("profile_id", profile_id)
                .execute()
            )
            if not deleted.data:
                raise LookupError("Note not found")
            return True

        return self._with_fallback_write(
            "delete_note",
            operation,
            self._fallback_delete_note(note_id),
            not_found_message="Note not found",
        )

    def get_resources(self, profile_id: str) -> list[dict[str, Any]]:
        def operation():
            resources = (
                get_app_schema_client()
                .from_("resources")
                .select("id, title, meta, category, icon, tone_class, is_locked")
                .order("title")
                .execute()
            ).data or []
            statuses = (
                get_app_schema_client()
                .from_("resource_statuses")
                .select("resource_id, label, tone, sort_order")
                .order("sort_order")
                .execute()
            ).data or []
            by_resource: dict[str, list[dict[str, Any]]] = {}
            for item in statuses:
                by_resource.setdefault(item["resource_id"], []).append(item)
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "meta": row["meta"],
                    "category": row["category"],
                    "statuses": [item["label"] for item in by_resource.get(row["id"], [])],
                    "tones": [item["tone"] for item in by_resource.get(row["id"], [])],
                    "icon": row["icon"],
                    "toneClass": row["tone_class"],
                    **({"locked": True} if row["is_locked"] else {}),
                }
                for row in resources
            ]

        return self._with_fallback("get_resources", operation, RESOURCES)

    def get_messages(self, profile_id: str) -> list[dict[str, Any]]:
        def operation():
            rows = (
                get_app_schema_client()
                .from_("support_messages")
                .select("id, sender_name, sender_avatar, sent_at, is_read, content, border_color")
                .eq("profile_id", profile_id)
                .order("sent_at", desc=True)
                .execute()
            ).data or []
            return [
                {
                    "id": row["id"],
                    "sender": row["sender_name"],
                    "senderAvatar": row["sender_avatar"],
                    "time": self._format_timestamp(row["sent_at"]),
                    "read": row["is_read"],
                    "content": row["content"],
                    "borderColor": row["border_color"],
                }
                for row in rows
            ]

        return self._with_fallback("get_messages", operation, MESSAGES)

    def create_message(self, profile_id: str, content: str) -> dict[str, Any]:
        def operation():
            inserted = (
                get_app_schema_client()
                .from_("support_messages")
                .insert(
                    {
                        "profile_id": profile_id,
                        "sender_name": "Adherent",
                        "sender_avatar": self.get_me(profile_id)["avatar"],
                        "content": content,
                        "is_read": False,
                        "border_color": "#22d3ff",
                    }
                )
                .execute()
            )
            row = self._single(inserted.data, "support message")
            return {
                "id": row["id"],
                "sender": row["sender_name"],
                "senderAvatar": row["sender_avatar"],
                "time": self._format_timestamp(row["sent_at"]),
                "read": row["is_read"],
                "content": row["content"],
                "borderColor": row["border_color"],
            }

        return self._with_fallback_write("create_message", operation, self._fallback_create_message(content))

    def mark_message_read(self, profile_id: str, message_id: str) -> dict[str, Any]:
        def operation():
            updated = (
                get_app_schema_client()
                .from_("support_messages")
                .update({"is_read": True})
                .eq("id", message_id)
                .eq("profile_id", profile_id)
                .execute()
            )
            row = self._single(updated.data, "support message")
            return {
                "id": row["id"],
                "sender": row["sender_name"],
                "senderAvatar": row["sender_avatar"],
                "time": self._format_timestamp(row["sent_at"]),
                "read": row["is_read"],
                "content": row["content"],
                "borderColor": row["border_color"],
            }

        fallback = self._fallback_mark_message_read(message_id)
        return self._with_fallback_write(
            "mark_message_read",
            operation,
            fallback,
            not_found_message="Message not found",
        )

    def get_coach_context(self, profile_id: str) -> dict[str, Any]:
        def operation():
            row = (
                get_app_schema_client()
                .from_("profiles")
                .select("current_step, current_step_label, current_score, target_score, deadline_label, toeic_date, weak_zones")
                .eq("id", profile_id)
                .limit(1)
                .execute()
            )
            data = self._single(row.data, "coach context")
            return {
                "etape": self._step_name_from_profile(data["current_step"], data["current_step_label"]),
                "score": data["current_score"],
                "objectif": data["target_score"],
                "deadline": self._resolve_deadline_label(data.get("toeic_date"), data["deadline_label"]).replace("TOEIC le ", ""),
                "weakZones": data["weak_zones"],
            }

        return self._with_fallback("get_coach_context", operation, COACH_CONTEXT.model_dump())

    def get_chat_history(self, profile_id: str) -> list[dict[str, Any]]:
        def operation():
            rows = (
                get_app_schema_client()
                .from_("chat_messages")
                .select("id, role, content, sent_at")
                .eq("profile_id", profile_id)
                .order("sent_at")
                .execute()
            ).data or []
            return [
                {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["sent_at"],
                }
                for row in rows
            ]

        return self._with_fallback("get_chat_history", operation, [item.model_dump() for item in CHAT_HISTORY])

    def persist_chat_message(self, profile_id: str, role: str, content: str) -> dict[str, Any]:
        try:
            inserted = (
                get_app_schema_client()
                .from_("chat_messages")
                .insert(
                    {
                        "profile_id": profile_id,
                        "role": role,
                        "content": content,
                    }
                )
                .execute()
            )
            row = self._single(inserted.data, "chat message")
            return {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["sent_at"],
            }
        except SupabaseNotConfiguredError:
            logger.info("supabase not configured, using fallback for persist_chat_message")
        except Exception as exc:
            logger.exception("supabase write failed for persist_chat_message: %s", exc)

        fallback = {
            "id": f"{role}-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
            "role": role,
            "content": content,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        CHAT_HISTORY.append(fallback)
        return fallback

    def _with_fallback(self, name: str, operation, fallback):
        try:
            return operation()
        except SupabaseNotConfiguredError:
            logger.info("supabase not configured, using fallback for %s", name)
            return fallback
        except Exception as exc:
            logger.exception("supabase read failed for %s: %s", name, exc)
            return fallback

    def _with_fallback_write(self, name: str, operation, fallback, not_found_message: str | None = None):
        try:
            return operation()
        except LookupError as exc:
            raise
        except SupabaseNotConfiguredError:
            logger.info("supabase not configured, using fallback for %s", name)
            return fallback
        except Exception as exc:
            logger.exception("supabase write failed for %s: %s", name, exc)
            return fallback

    @staticmethod
    def _single(rows: list[dict[str, Any]] | None, label: str) -> dict[str, Any]:
        if not rows:
            raise LookupError(f"{label} not found")
        return rows[0]

    @staticmethod
    def _note_meta(updated_at: str | None = None) -> str:
        if updated_at:
            value = updated_at[:10]
        else:
            value = datetime.now(tz=timezone.utc).date().isoformat()
        return f"Mise a jour le {value}"

    @staticmethod
    def _format_timestamp(value: str) -> str:
        return value.replace("T", " ")[:16]

    @staticmethod
    def _split_total_score(total_score: int) -> tuple[int, int]:
        listening = max(0, min(495, ((total_score // 2) // 5) * 5))
        reading = max(0, min(495, total_score - listening))
        reading = ((reading + 2) // 5) * 5
        diff = total_score - (listening + reading)
        reading += diff
        if reading > 495:
            overflow = reading - 495
            reading = 495
            listening = max(0, listening - overflow)
        if listening > 495:
            overflow = listening - 495
            listening = 495
            reading = max(0, reading - overflow)
        return listening, reading

    @staticmethod
    def _deadline_label_from_date(toeic_date: str) -> str:
        try:
            target = datetime.fromisoformat(toeic_date).date()
        except ValueError:
            return f"TOEIC le {toeic_date}"
        today = datetime.now(tz=timezone.utc).date()
        delta = (target - today).days
        if delta > 0:
            return f"J-{delta}"
        if delta == 0:
            return "Aujourd'hui"
        return f"TOEIC le {toeic_date}"

    @classmethod
    def _resolve_deadline_label(cls, toeic_date: str | None, deadline_label: str) -> str:
        if toeic_date:
            return cls._deadline_label_from_date(toeic_date)
        return deadline_label

    @staticmethod
    def _compute_progression_percent(progression: list[dict[str, Any]]) -> int:
        if not progression:
            return 0
        total = 0
        for item in progression:
            if item.get("progress_percent") is not None:
                total += item["progress_percent"]
            elif item.get("status_label") == "Completee":
                total += 100
        return round(total / len(progression))

    @staticmethod
    def _step_name_from_profile(step_number: int | None, current_step_label: str) -> str:
        mapping = {
            1: "Embarquement",
            2: "Listening",
            3: "Reading",
            4: "Deep Boost 2.0",
            5: "Anti Derangement",
        }
        if step_number in mapping:
            return mapping[step_number]
        return current_step_label

    @staticmethod
    def _map_note(note: dict[str, Any], words: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": note["id"],
            "title": note["title"],
            "meta": note.get("meta") or AdherentRepository._note_meta(note.get("updated_at")),
            "etape": note.get("step_label", ""),
            "content": note.get("content", ""),
            "words": [{"word": item["word"], "state": item.get("state", "")} for item in words],
            **({"tag": note["tag"]} if note.get("tag") else {}),
        }

    def _fallback_create_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        for item in SCORES["history"]:
            item["isCurrent"] = False
        row = {
            "date": datetime.now(tz=timezone.utc).date().isoformat(),
            "listening": payload["listening"],
            "reading": payload["reading"],
            "total": payload["listening"] + payload["reading"],
            "format": payload["format"],
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

    def _fallback_create_note(self, payload: dict[str, Any]) -> dict[str, Any]:
        note = {
            "id": f"note-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
            "title": payload.get("title") or "Nouvelle note",
            "meta": self._note_meta(),
            "etape": payload.get("etape") or "",
            "content": payload.get("content") or "",
            "words": payload.get("words") or [],
            "tag": payload.get("tag"),
        }
        NOTES.insert(0, note)
        return note

    def _fallback_update_note(self, note_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for note in NOTES:
            if note["id"] == note_id:
                if payload.get("title") is not None:
                    note["title"] = payload["title"]
                if payload.get("etape") is not None:
                    note["etape"] = payload["etape"]
                if payload.get("content") is not None:
                    note["content"] = payload["content"]
                if payload.get("words") is not None:
                    note["words"] = payload["words"]
                if "tag" in payload:
                    note["tag"] = payload.get("tag")
                note["meta"] = self._note_meta()
                return note
        raise LookupError("Note not found")

    @staticmethod
    def _fallback_delete_note(note_id: str) -> bool:
        for index, note in enumerate(NOTES):
            if note["id"] == note_id:
                NOTES.pop(index)
                return True
        raise LookupError("Note not found")

    def _fallback_create_message(self, content: str) -> dict[str, Any]:
        message = {
            "id": f"msg-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
            "sender": "Adherent",
            "senderAvatar": ADHERENT_USER.avatar,
            "time": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "read": False,
            "content": content,
            "borderColor": "#22d3ff",
        }
        MESSAGES.insert(0, message)
        return message

    def _fallback_dashboard_after_init(self, payload: dict[str, Any]) -> dict[str, Any]:
        listening, reading = self._split_total_score(payload["currentScore"])
        return {
            **DASHBOARD_DATA,
            "score": payload["currentScore"],
            "scoreStart": payload["currentScore"],
            "scoreObjectif": payload["targetScore"],
            "listening": listening,
            "reading": reading,
        }

    def _fallback_coach_context_after_init(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **COACH_CONTEXT.model_dump(),
            "score": payload["currentScore"],
            "objectif": payload["targetScore"],
            "deadline": self._deadline_label_from_date(payload["toeicDate"]).replace("TOEIC le ", ""),
        }

    @staticmethod
    def _fallback_mark_message_read(message_id: str) -> dict[str, Any]:
        for message in MESSAGES:
            if message["id"] == message_id:
                message["read"] = True
                return message
        raise LookupError("Message not found")
