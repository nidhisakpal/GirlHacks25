import asyncio
import logging
import os
from typing import List, Optional

import google.generativeai as genai

from app.database import add_chat_message, append_intents, get_chat_history, get_user, update_user_goddess
from app.goddess_matcher import GoddessMatcher
from app.models import ChatMessage, ChatResponse, Citation, IntentPrediction
from app.search_service import SearchService

from datetime import datetime, timedelta, timezone
from collections import Counter  # deque removed


LOGGER = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("models/gemini-2.5-flash")

    async def generate(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()

        def _run() -> str:
            response = self._model.generate_content(prompt)
            return getattr(response, "text", "").strip()

        return await loop.run_in_executor(None, _run)


class IntentClassifier:
    """Lightweight keyword classifier with extensibility for LLM refinement."""

    KEYWORDS = {
        "academics": [
            "class",
            "course",
            "study",
            "exam",
            "professor",
            "grade",
            "tutor",
            "research",
        ],
        "career": [
            "internship",
            "job",
            "career",
            "resume",
            "interview",
            "handshake",
            "co-op",
            "salary",
        ],
        "events": [
            "event",
            "workshop",
            "club",
            "meetup",
            "hackathon",
            "seminar",
            "career fair",
        ],
        "wellbeing": [
            "stress",
            "wellness",
            "mental",
            "therapy",
            "health",
            "burnout",
            "sleep",
            "balance",
        ],
    }

    DEFAULT_INTENT = "academics"

    async def predict(self, message: str) -> IntentPrediction:
        text = message.lower()
        best_intent = self.DEFAULT_INTENT
        best_score = 0
        best_hits: List[str] = []

        for intent, keywords in self.KEYWORDS.items():
            hits = [keyword for keyword in keywords if keyword in text]
            score = len(hits)
            if score > best_score:
                best_intent = intent
                best_score = score
                best_hits = hits

        if best_score == 0:
            rationale = ["no strong keyword match; defaulting to academics"]
        else:
            rationale = [f"matched '{kw}'" for kw in best_hits]

        confidence = 0.35 + 0.15 * best_score
        return IntentPrediction(intent=best_intent, confidence=min(confidence, 0.95), rationale=rationale)


class ChatService:
    def __init__(
        self,
        matcher: Optional[GoddessMatcher] = None,
        search_service: Optional[SearchService] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        self._gaia_persona = (
            "You are Gaia, the nurturing heart of NJIT mentorship. Welcome the student warmly, "
            "explain that your daughters specialize in different kinds of support, and briefly "
            "summarize what each goddess offers:\n"
            "- Athena: wisdom for courses and academic planning\n"
            "- Aphrodite: confidence, community, mental wellness\n"
            "- Artemis: mentorship, internships, scholarships\n"
            "- Tyche: funding, grants, financial opportunities\n"
            "Invite the student to share what they need so you can match them."
        )
        self._matcher = matcher or GoddessMatcher()
        self._search = search_service or SearchService()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._gemini = gemini_client or GeminiClient()

        # Switching policy knobs
        self._suggest_min_conf = 0.51   # τ: minimum classifier confidence
        self._wins_window = 5           # M: window size
        self._wins_needed = 2           # N: require same winner ≥ N in last M turns
        self._handoff_cooldown = timedelta(hours=6)  # snooze after a decline

        personas = self._matcher.personas()
        self._persona_lookup = {
            **personas,
            "gaia": {
                "id": "gaia",
                "display_name": "Gaia",
                "persona": self._gaia_persona,
                "tagline": "Nurturing mother of NJIT goddesses.",
            },
        }

    def _get_routing_state(self, user):
        rs = getattr(user, "routing_state", None) or {}
        wins = rs.get("win_history", [])
        declined = rs.get("declined", {})  # { goddess: iso8601 }
        wins = list(wins)[-self._wins_window:]
        return {"win_history": wins, "declined": dict(declined)}

    async def _save_routing_state(self, db, user_id: str, rs: dict):
        # piggyback on update_user_goddess to persist small state blob
        await update_user_goddess(
            db, user_id,
            None,  # keep current selected_goddess unchanged
            quiz_results=None,
            suggested=None,
            handoff_stage=None,
            routing_state=rs
        )

    async def get_response(self, user_id: str, message: str, db) -> ChatResponse:
        user = await get_user(db, user_id)
        if not user:
            raise ValueError("User profile not found")

        active_goddess = user.selected_goddess or "gaia"
        stage = user.handoff_stage
        suggested = user.suggested_goddess

        history = await get_chat_history(db, user_id)

        # Log the user's message in the current thread
        user_entry = await add_chat_message(
            db, user_id, role="user", content=message, goddess=active_goddess
        )
        thread_messages = history.messages.get(active_goddess, [])
        recent_messages = thread_messages[-6:] + [user_entry]

        # ---------- 1) If we're awaiting confirmation, block everything except yes/no ----------
        if stage == "awaiting_confirmation" and suggested:
            return ChatResponse(
                message=(
                    f"I can connect you with {self._persona_lookup.get(suggested, {}).get('display_name', suggested.title())}."
                ),
                goddess=active_goddess,
                intent="handoff_request",
                citations=[],
                trace={
                    "stage": "awaiting_confirmation",
                    "suggested": suggested,
                    "current_goddess": active_goddess,
                },
            )

        # ---------- 2) Classify, match, and possibly request confirmation ----------
        intent_prediction = await self._intent_classifier.predict(message)
        match_result = self._matcher.match_for_message(message, intent_prediction.intent)

        # --- ROUTING STATE UPDATE & DECISION GATES ---
        rs = self._get_routing_state(user)

        # push current winner (candidate or current)
        winner = match_result.goddess or active_goddess
        rs["win_history"] = (rs.get("win_history", []) + [winner])[-self._wins_window:]

        # persistence: how often did this candidate win recently?
        wins = Counter(rs["win_history"])
        wins_for_suggested = wins.get(match_result.goddess, 0)

        # cooldown after declines
        declined = rs.get("declined", {})
        declined_iso = declined.get(match_result.goddess)
        declined_recently = False
        if declined_iso:
            try:
                t = datetime.fromisoformat(str(declined_iso).replace("Z", "+00:00"))
                declined_recently = (datetime.now(timezone.utc) - t) < self._handoff_cooldown
            except Exception:
                declined_recently = False

        # gated suggestion rule
        should_suggest = (
            match_result.goddess
            and match_result.goddess != active_goddess
            and intent_prediction.confidence >= self._suggest_min_conf  # confidence floor τ
            and wins_for_suggested >= self._wins_needed                  # persistence N-of-M
            and not declined_recently                                    # decline cooldown
        )

        if should_suggest:
            await update_user_goddess(
                db,
                user_id,
                active_goddess,  # do not switch yet
                quiz_results=user.quiz_results or {},
                suggested=match_result.goddess,
                handoff_stage="awaiting_confirmation",
            )
            # clear cooldown for this goddess (we're explicitly asking again after evidence)
            rs.get("declined", {}).pop(match_result.goddess, None)
            await self._save_routing_state(db, user_id, rs)
            return ChatResponse(
                message=(
                    f"I can connect you with {self._persona_lookup.get(match_result.goddess, {}).get('display_name', match_result.goddess.title())}. "
                    "Shall I introduce you?"
                ),
                goddess=active_goddess,
                intent="handoff_request",
                citations=[],
                trace={
                    "intent": intent_prediction.model_dump(),
                    "match": match_result.model_dump(),
                    "stage": "awaiting_confirmation",
                    "suggested": match_result.goddess,
                    "current_goddess": active_goddess,
                },
            )

        # persist updated window even if we didn’t suggest
        await self._save_routing_state(db, user_id, rs)

        # ---------- 3) Normal flow (we have permission to continue) ----------
        citations = await self._search.search(message, intent_prediction.intent)
        persona = self._persona_lookup.get(active_goddess, {})
        goddess_name = persona.get("display_name", active_goddess.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        prompt = self._build_prompt(
            persona_prompt, goddess_name, recent_messages, message, citations
        )
        llm_text = await self._gemini.generate(prompt)
        response_text = self._post_process(llm_text)

        await append_intents(db, user_id, [intent_prediction.intent])
        await add_chat_message(
            db,
            user_id,
            role="assistant",
            content=response_text,
            goddess=active_goddess,
            intent=intent_prediction.intent,
            citations=citations,
        )

        return ChatResponse(
            message=response_text,
            goddess=active_goddess,
            intent=intent_prediction.intent,
            citations=citations,
            trace={
                "intent": intent_prediction.model_dump(),
                "match": match_result.model_dump(),
                "current_goddess": active_goddess,
                "stage": "confirmed" if stage == "confirmed" else None,
            },
        )

    def _build_prompt(
        self,
        persona_prompt: str,
        goddess_name: str,
        history: List[ChatMessage],
        latest_message: str,
        citations: List[Citation],
    ) -> str:
        citation_lines = []
        for idx, citation in enumerate(citations, start=1):
            citation_lines.append(
                f"[{idx}] {citation.title} - {citation.snippet[:220]} (Source: {citation.source}) {citation.url}"
            )
        if not citation_lines:
            citation_lines.append("No resources matched. If the topic requires facts, acknowledge the gap.")

        history_lines: List[str] = []
        for message in history[-5:]:
            speaker = goddess_name if message.role == "assistant" else "Student"
            history_lines.append(f"{speaker}: {message.content.strip()}")

        prompt = (
            f"{persona_prompt}\n\n"
            "You mentor an NJIT student. Respond in the goddess's voice, precise and encouraging.\n"
            "Ground every factual statement in the provided resources. When you cite, use inline "
            "brackets like [1]. Offer next steps and keep responses under 180 words.\n"
            "If resources are missing for the request, state that you will follow up after "
            "checking with campus partners.\n\n"
            f"Resources:\n{'\n'.join(citation_lines)}\n\n"
            f"Conversation so far:\n{'\n'.join(history_lines)}\n\n"
            f"Student: {latest_message.strip()}\n"
            f"{goddess_name}:"
        )
        return prompt

    async def confirm_handoff(self, user_id: str, db) -> ChatResponse:
        user = await get_user(db, user_id)
        if not user or not user.suggested_goddess:
            active = (user.selected_goddess if user else "gaia") or "gaia"
            return ChatResponse(
                message="No handoff is pending.",
                goddess=active,
                intent="handoff_none",
                citations=[],
                trace={"stage": None, "current_goddess": active},
            )

        # Switch to suggested goddess
        new_goddess = user.suggested_goddess
        await update_user_goddess(
            db,
            user_id,
            new_goddess,
            quiz_results=user.quiz_results or {},
            suggested=None,
            handoff_stage=None,
        )

        # reset decline cooldown for the new goddess; keep win history rolling
        rs = self._get_routing_state(user)
        rs.get("declined", {}).pop(new_goddess, None)
        await self._save_routing_state(db, user_id, rs)

        # Generate a short welcome/continuation as the new goddess
        history = await get_chat_history(db, user_id)
        thread_messages = history.messages.get(new_goddess, [])
        recent_messages = thread_messages[-5:]  # context for continuity

        persona = self._persona_lookup.get(new_goddess, {})
        goddess_name = persona.get("display_name", new_goddess.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        prompt = (
            f"{persona_prompt}\n\n"
            f"You have just been introduced to the student via a handoff. "
            f"Briefly (<=80 words) greet them as {goddess_name}, confirm you’ll help, and ask one precise follow-up question."
        )

        llm_text = await self._gemini.generate(prompt)
        response_text = self._post_process(llm_text)

        await add_chat_message(
            db,
            user_id,
            role="assistant",
            content=response_text,
            goddess=new_goddess,
            intent="handoff_welcome",
            citations=[],
        )

        return ChatResponse(
            message=response_text,
            goddess=new_goddess,
            intent="handoff_welcome",
            citations=[],
            trace={"stage": None, "current_goddess": new_goddess},
        )

    async def decline_handoff(self, user_id: str, db) -> ChatResponse:
        user = await get_user(db, user_id)
        active = user.selected_goddess if user and user.selected_goddess else "gaia"

        # Clear suggestion and stay on current goddess
        await update_user_goddess(
            db,
            user_id,
            active,
            quiz_results=user.quiz_results or {},
            suggested=None,
            handoff_stage=None,
        )

        # Gentle acknowledgement from current goddess
        persona = self._persona_lookup.get(active, {})
        goddess_name = persona.get("display_name", active.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")
        prompt = (
            f"{persona_prompt}\n\n"
            f"As {goddess_name}, acknowledge the choice kindly (<=40 words) and continue support."
        )
        llm_text = await self._gemini.generate(prompt)
        response_text = self._post_process(llm_text)

        await add_chat_message(
            db,
            user_id,
            role="assistant",
            content=response_text,
            goddess=active,
            intent="handoff_declined",
            citations=[],
        )

        # mark a short-lived decline cooldown for that suggested goddess
        rs = self._get_routing_state(user)
        if user.suggested_goddess:
            rs.setdefault("declined", {})[user.suggested_goddess] = datetime.now(timezone.utc).isoformat()
        await self._save_routing_state(db, user_id, rs)

        return ChatResponse(
            message=response_text,
            goddess=active,
            intent="handoff_declined",
            citations=[],
            trace={"stage": None, "current_goddess": active},
        )

    @staticmethod
    def _post_process(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("\n"):
            cleaned = cleaned.lstrip()
        return cleaned
