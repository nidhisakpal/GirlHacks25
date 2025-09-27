import asyncio
import logging
import os
from typing import List, Optional

import google.generativeai as genai

from app.database import add_chat_message, append_intents, get_chat_history, get_user
from app.goddess_matcher import GoddessMatcher
from app.models import ChatMessage, ChatResponse, Citation, IntentPrediction
from app.search_service import SearchService

LOGGER = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-pro")

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
        self._matcher = matcher or GoddessMatcher()
        self._search = search_service or SearchService()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._gemini = gemini_client or GeminiClient()
        personas = self._matcher.personas()
        self._persona_lookup = {pid: data for pid, data in personas.items()}

    async def get_response(self, user_id: str, message: str, db) -> ChatResponse:
        user = await get_user(db, user_id)
        if not user:
            raise ValueError("User profile not found")

        history = await get_chat_history(db, user_id)

        user_entry = await add_chat_message(
            db,
            user_id,
            role="user",
            content=message,
        )

        recent_messages = history.messages + [user_entry]
        recent_messages = recent_messages[-6:]

        intent_prediction = await self._intent_classifier.predict(message)
        match_result = self._matcher.match_for_message(message, intent_prediction.intent)
        citations = await self._search.search(message, intent_prediction.intent)

        goddess_id = match_result.goddess
        persona = self._persona_lookup.get(goddess_id, {})
        goddess_name = persona.get("display_name", goddess_id.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        prompt = self._build_prompt(
            persona_prompt,
            goddess_name,
            recent_messages,
            message,
            citations,
        )

        llm_text = await self._gemini.generate(prompt)
        response_text = self._post_process(llm_text)

        await append_intents(db, user_id, [intent_prediction.intent])

        await add_chat_message(
            db,
            user_id,
            role="assistant",
            content=response_text,
            goddess=goddess_id,
            intent=intent_prediction.intent,
            citations=citations,
        )

        return ChatResponse(
            message=response_text,
            goddess=goddess_id,
            intent=intent_prediction.intent,
            citations=citations,
            trace={
                "intent": intent_prediction.model_dump(),
                "match": match_result.model_dump(),
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

    @staticmethod
    def _post_process(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("\n"):
            cleaned = cleaned.lstrip()
        return cleaned

