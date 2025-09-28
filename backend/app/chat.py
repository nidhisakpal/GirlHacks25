import asyncio
import logging
import os
from typing import List, Optional

import google.generativeai as genai

from app.database import add_chat_message, append_intents, get_chat_history, get_user, update_user_goddess
from app.goddess_matcher import GoddessMatcher
from app.models import ChatMessage, ChatResponse, Citation, IntentPrediction, MatchResult
from app.search_service import SearchService

from datetime import datetime, timedelta, timezone

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
            "class", "course", "study", "exam", "professor", "grade", "tutor", "research",
        ],
        "career": [
            "internship", "job", "career", "resume", "interview", "handshake", "co-op", "salary",
        ],
        "events": [
            "event", "workshop", "club", "meetup", "hackathon", "seminar", "career fair",
        ],
        "wellbeing": [
            "stress", "wellness", "mental", "therapy", "health", "burnout", "sleep", "balance",
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

        # Routing thresholds tuned for matcher scores
        self._auto_switch_threshold = 2.5  # raw matcher score needed to auto-switch
        self._handoff_suggest_threshold = 1.6  # score that triggers a handoff suggestion
        self._intent_suggestion_floor = 0.55  # classifier confidence that supports a suggestion

        self._switching_cues = [
            "switch",
            "change",
            "different",
            "another",
            "someone else",
            "career help",
            "job",
            "internship",
            "stress",
            "mental health",
            "burnout",
            "wellness",
            "money",
            "funding",
            "scholarship",
            "grant",
        ]

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

    async def get_response(self, user_id: str, message: str, db) -> ChatResponse:
        user = await get_user(db, user_id)
        if not user:
            raise ValueError("User profile not found")

        current_goddess = user.selected_goddess or "gaia"
        
        # Handle pending confirmations first
        if user.handoff_stage == "awaiting_confirmation":
            return await self._handle_confirmation_response(user_id, message, db, user)

        # Classify intent and find best match for routing
        intent_prediction = await self._intent_classifier.predict(message)
        match_result = self._matcher.match_for_message(message, intent_prediction.intent)
        decision = self._decide_routing(
            current_goddess, match_result, intent_prediction.confidence, message
        )
        target_goddess = decision["target"]
        suggested_goddess = decision.get("suggested")

        # Log user message
        history = await get_chat_history(db, user_id)
        user_entry = await add_chat_message(
            db, user_id, role="user", content=message, goddess=target_goddess
        )

        # Build conversation context for the reply
        thread_messages = history.messages.get(target_goddess, [])
        recent_messages = thread_messages[-6:] + [user_entry]

        citations = await self._search.search(message, intent_prediction.intent)

        routing_state_payload = None
        if decision["mode"] == "suggest" and suggested_goddess:
            routing_state_payload = {
                "score": match_result.confidence,
                "intent": intent_prediction.intent,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if citations:
                routing_state_payload["citations"] = [citation.model_dump() for citation in citations]
            if match_result.rationale:
                routing_state_payload["rationale"] = match_result.rationale

        if decision["mode"] == "suggest" and suggested_goddess:
            response_text = await self._generate_handoff_suggestion(
                target_goddess,
                suggested_goddess,
                recent_messages,
                message,
                citations,
                match_result.rationale,
            )
            response_intent = "handoff_request"
        else:
            response_text = await self._generate_response(
                target_goddess, recent_messages, message, citations
            )
            response_intent = intent_prediction.intent

        update_kwargs = {}
        if decision["mode"] == "switch":
            update_kwargs = {
                "goddess": target_goddess,
                "suggested": None,
                "handoff_stage": None,
                "routing_state": None,
            }
        elif decision["mode"] == "suggest" and suggested_goddess:
            update_kwargs = {
                "goddess": target_goddess,
                "suggested": suggested_goddess,
                "handoff_stage": "awaiting_confirmation",
                "routing_state": routing_state_payload,
            }
        elif not user.selected_goddess:
            update_kwargs = {
                "goddess": target_goddess,
                "suggested": None,
                "handoff_stage": None,
                "routing_state": None,
            }

        if update_kwargs:
            await update_user_goddess(
                db,
                user_id,
                quiz_results=user.quiz_results or {},
                **update_kwargs,
            )

        await append_intents(db, user_id, [intent_prediction.intent])
        await add_chat_message(
            db,
            user_id,
            role="assistant",
            content=response_text,
            goddess=target_goddess,
            intent=response_intent,
            citations=citations,
        )

        trace = {
            "intent": intent_prediction.model_dump(),
            "match": match_result.model_dump(),
            "mode": decision["mode"],
            "previous_goddess": current_goddess,
            "current_goddess": target_goddess,
            "switched": decision["mode"] == "switch",
        }
        if decision["mode"] == "suggest" and suggested_goddess:
            trace.update(
                {
                    "stage": "awaiting_confirmation",
                    "suggested": suggested_goddess,
                    "handoff_reason": match_result.rationale,
                }
            )

        return ChatResponse(
            message=response_text,
            goddess=target_goddess,
            intent=response_intent,
            citations=citations,
            trace=trace,
        )

    def _decide_routing(
        self,
        current: str,
        match_result: MatchResult,
        intent_confidence: float,
        message: str,
    ) -> dict:
        """Choose whether to stay with the current goddess or request a handoff."""

        decision = {"mode": "stay", "target": current, "suggested": None}
        suggested = match_result.goddess
        if not suggested or suggested == current:
            return decision

        score = match_result.confidence or 0.0
        message_lower = message.lower()
        explicit_switch = any(cue in message_lower for cue in self._switching_cues)
        has_intent_signal = intent_confidence >= self._intent_suggestion_floor

        should_consider = (
            score >= self._handoff_suggest_threshold
            or explicit_switch
            or has_intent_signal
        )
        if not should_consider:
            return decision

        if score >= self._auto_switch_threshold or (
            explicit_switch and score >= self._handoff_suggest_threshold
        ):
            decision.update({"mode": "switch", "target": suggested})
            return decision

        decision.update({"mode": "suggest", "suggested": suggested})
        return decision

    async def _handle_confirmation_response(self, user_id: str, message: str, db, user) -> ChatResponse:
        """Handle yes/no responses to handoff suggestions."""
        message_lower = message.lower().strip()

        # Yes responses
        if any(word in message_lower for word in ["yes", "y", "ok", "sure", "please", "go ahead"]):
            return await self.confirm_handoff(user_id, db)
        
        # No responses  
        if any(word in message_lower for word in ["no", "n", "not", "stay", "keep"]):
            return await self.decline_handoff(user_id, db)
        
        # Unclear response - ask for clarification
        current = user.selected_goddess or "gaia"
        suggested_name = self._persona_lookup.get(user.suggested_goddess, {}).get('display_name', 'specialist')
        
        return ChatResponse(
            message=f"Would you like me to connect you with {suggested_name}? Please say 'yes' or 'no'.",
            goddess=current,
            intent="handoff_clarification",
            citations=[],
            trace={
                "stage": "awaiting_confirmation",
                "needs_clarification": True,
                "suggested": user.suggested_goddess,
            }
        )

    def _format_citation_lines(self, citations: List[Citation]) -> List[str]:
        lines = []
        for idx, citation in enumerate(citations, start=1):
            lines.append(
                f"[{idx}] {citation.title} - {citation.snippet[:220]} (Source: {citation.source}) {citation.url}"
            )
        if not lines:
            lines.append(
                "Azure Search returned no matching resources. Let the student know you'll investigate and follow up."
            )
        return lines

    def _format_history_lines(
        self, goddess_name: str, history: List[ChatMessage]
    ) -> List[str]:
        lines: List[str] = []
        for msg in history[-5:]:
            speaker = goddess_name if msg.role == "assistant" else "Student"
            lines.append(f"{speaker}: {msg.content.strip()}")
        return lines

    async def _generate_response(
        self, goddess: str, history: List[ChatMessage], message: str, citations: List[Citation]
    ) -> str:
        """Generate response using the specified goddess persona."""

        persona = self._persona_lookup.get(goddess, {})
        goddess_name = persona.get("display_name", goddess.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        citation_lines = self._format_citation_lines(citations)
        history_lines = self._format_history_lines(goddess_name, history)

        prompt = (
            f"{persona_prompt}\n\n"
            "You mentor an NJIT student. Respond in the goddess's voice, precise and encouraging.\n"
            "Ground every factual statement in the provided resources. When you cite, use inline "
            "brackets like [1]. Offer next steps and keep responses under 180 words.\n"
            "If resources are missing for the request, state that you will follow up after "
            "checking with campus partners.\n\n"
            f"Resources:\n{chr(10).join(citation_lines)}\n\n"
            f"Conversation so far:\n{chr(10).join(history_lines)}\n\n"
            f"Student: {message.strip()}\n"
            f"{goddess_name}:"
        )

        return await self._gemini.generate(prompt)

    async def _generate_handoff_suggestion(
        self,
        current_goddess: str,
        suggested_goddess: str,
        history: List[ChatMessage],
        message: str,
        citations: List[Citation],
        rationale: List[str],
    ) -> str:
        """Prompt the current goddess to propose a handoff to a specialist."""

        current_persona = self._persona_lookup.get(current_goddess, {})
        current_name = current_persona.get("display_name", current_goddess.title())
        current_prompt = current_persona.get("persona", "You are a helpful mentor.")

        suggested_persona = self._persona_lookup.get(suggested_goddess, {})
        suggested_name = suggested_persona.get(
            "display_name", suggested_goddess.title()
        )
        suggested_tagline = suggested_persona.get("tagline", "specialist support")

        handoff_reason = "; ".join(rationale) if rationale else "They specialise in this topic."

        citation_lines = self._format_citation_lines(citations)
        history_lines = self._format_history_lines(current_name, history)

        prompt = (
            f"{current_prompt}\n\n"
            "You mentor an NJIT student. You believe another goddess is better suited to assist.\n"
            "Write under 150 words, stay warm, and keep a mentoring tone.\n"
            f"Explain why {suggested_name} ({suggested_tagline}) fits best, citing resources with [#] if you reference them.\n"
            f"Reasoning: {handoff_reason}.\n"
            "Ask clearly if the student wants to be connected (yes/no).\n"
            "If resources are missing, say you'll gather more.\n\n"
            f"Resources:\n{chr(10).join(citation_lines)}\n\n"
            f"Conversation so far:\n{chr(10).join(history_lines)}\n\n"
            f"Student: {message.strip()}\n"
            f"{current_name}:"
        )

        return await self._gemini.generate(prompt)

    async def confirm_handoff(self, user_id: str, db) -> ChatResponse:
        """Confirm and execute handoff to suggested goddess."""
        user = await get_user(db, user_id)
        if not user or not user.suggested_goddess:
            current = user.selected_goddess if user else "gaia"
            return ChatResponse(
                message="No handoff is pending.",
                goddess=current, intent="handoff_none", citations=[],
                trace={"stage": None, "current_goddess": current}
            )

        previous = user.selected_goddess or "gaia"
        new_goddess = user.suggested_goddess
        routing_state = getattr(user, "routing_state", None) or {}
        intent_hint = routing_state.get("intent")
        message_text = routing_state.get("message")
        rationale = routing_state.get("rationale") or []

        history = await get_chat_history(db, user_id)

        if not message_text:
            previous_thread = history.messages.get(previous, [])
            for msg in reversed(previous_thread):
                if msg.role == "user":
                    message_text = msg.content
                    break
        if not message_text:
            message_text = "I need help following up on my last question."

        citations_payload = routing_state.get("citations") or []
        citations: List[Citation] = []
        try:
            citations = [Citation(**item) for item in citations_payload]
        except Exception:
            citations = []

        if not citations:
            citations = await self._search.search(message_text, intent_hint)

        await update_user_goddess(
            db, user_id, new_goddess,
            quiz_results=user.quiz_results or {},
            suggested=None, handoff_stage=None, routing_state=None
        )

        thread_messages = history.messages.get(new_goddess, [])
        user_entry = await add_chat_message(
            db, user_id, role="user", content=message_text, goddess=new_goddess
        )

        recent_messages = thread_messages[-6:] + [user_entry]
        response_text = await self._generate_response(
            new_goddess, recent_messages, message_text, citations
        )
        response_intent = intent_hint or "handoff_confirmed"

        await append_intents(db, user_id, [response_intent])
        await add_chat_message(
            db, user_id, role="assistant", content=response_text,
            goddess=new_goddess, intent=response_intent, citations=citations
        )

        trace = {
            "stage": None,
            "current_goddess": new_goddess,
            "previous_goddess": previous,
            "switched": True,
            "mode": "switch",
            "confirmed": True,
        }
        if rationale:
            trace["handoff_reason"] = rationale

        return ChatResponse(
            message=response_text,
            goddess=new_goddess,
            intent=response_intent,
            citations=citations,
            trace=trace,
        )

    async def decline_handoff(self, user_id: str, db) -> ChatResponse:
        """Decline handoff and stay with current goddess."""
        user = await get_user(db, user_id)
        current = user.selected_goddess if user and user.selected_goddess else "gaia"

        # Clear suggestion
        await update_user_goddess(
            db, user_id, current,
            quiz_results=user.quiz_results or {},
            suggested=None, handoff_stage=None, routing_state=None
        )

        # Generate acknowledgment
        response_text = await self._generate_decline_acknowledgment(current)
        
        await add_chat_message(
            db, user_id, role="assistant", content=response_text,
            goddess=current, intent="handoff_declined", citations=[]
        )

        return ChatResponse(
            message=response_text,
            goddess=current,
            intent="handoff_declined",
            citations=[],
            trace={
                "stage": None,
                "current_goddess": current,
                "switched": False,
                "mode": "stay",
            }
        )

    async def _generate_handoff_welcome(self, goddess: str) -> str:
        """Generate welcome message for new goddess."""
        persona = self._persona_lookup.get(goddess, {})
        goddess_name = persona.get("display_name", goddess.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        prompt = (
            f"{persona_prompt}\n\n"
            f"You have just been introduced to the student. "
            f"Briefly (<=80 words) greet them as {goddess_name}, confirm you'll help, "
            f"and ask one precise follow-up question to understand their needs better."
        )
        
        return await self._gemini.generate(prompt)

    async def _generate_decline_acknowledgment(self, goddess: str) -> str:
        """Generate acknowledgment for declined handoff."""
        persona = self._persona_lookup.get(goddess, {})
        goddess_name = persona.get("display_name", goddess.title())
        persona_prompt = persona.get("persona", "You are a helpful mentor.")

        prompt = (
            f"{persona_prompt}\n\n"
            f"As {goddess_name}, acknowledge the student's choice to continue with you "
            f"kindly (<=40 words) and offer continued support."
        )
        
        return await self._gemini.generate(prompt)
