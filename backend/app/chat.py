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
    """Gemini-powered intent classifier for better understanding of user needs."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self._gemini = gemini_client or GeminiClient()

    async def predict(self, message: str) -> IntentPrediction:
        """Use Gemini to classify user intent and suggest appropriate goddess."""
        
        prompt = f"""You are an AI assistant that helps route NJIT students to the right mentor based on their needs.

Available mentors and their specialties:
- **Athena**: Academic help (courses, study, research, grades, homework, projects, professors, tutoring)
- **Aphrodite**: Mental health & wellness (stress, anxiety, depression, self-esteem, relationships, counseling, therapy)
- **Artemis**: Career & professional development (jobs, internships, mentorships, networking, resumes, interviews)
- **Tyche**: Financial aid & scholarships (funding, grants, tuition, financial planning, emergency aid)
- **Gaia**: General guidance and initial routing

Student message: "{message}"

Analyze the student's message and determine:
1. Primary intent (academics, wellbeing, career, scholarships, or general)
2. Most appropriate goddess to help
3. Confidence level (0.0-1.0)
4. Brief reasoning

Respond in this exact JSON format:
{{
    "intent": "academics|wellbeing|career|scholarships|general",
    "suggested_goddess": "athena|aphrodite|artemis|tyche|gaia",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this classification was chosen"
}}

Consider:
- Multiple topics in one message (choose the primary concern)
- Emotional context and urgency
- Specific vs general requests
- Academic stress vs mental health concerns
- Career questions vs academic questions"""

        try:
            response = await self._gemini.generate(prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                return IntentPrediction(
                    intent=result.get("intent", "general"),
                    confidence=float(result.get("confidence", 0.7)),
                    rationale=[result.get("reasoning", "Gemini classification")],
                    suggested_goddess=result.get("suggested_goddess")
                )
            else:
                # Fallback if JSON parsing fails
                return IntentPrediction(
                    intent="general",
                    confidence=0.5,
                    rationale=["Failed to parse Gemini response"]
                )
                
        except Exception as e:
            # Fallback to simple keyword matching if Gemini fails
            return await self._fallback_classify(message)

    async def _fallback_classify(self, message: str) -> IntentPrediction:
        """Fallback keyword-based classification if Gemini fails."""
        text = message.lower()
        
        # Simple keyword matching as fallback
        if any(word in text for word in ["stress", "anxiety", "depression", "mental", "therapy", "counseling", "wellness"]):
            return IntentPrediction(intent="wellbeing", confidence=0.7, rationale=["Fallback: mental health keywords"])
        elif any(word in text for word in ["job", "career", "internship", "resume", "interview", "mentor"]):
            return IntentPrediction(intent="career", confidence=0.7, rationale=["Fallback: career keywords"])
        elif any(word in text for word in ["scholarship", "money", "funding", "tuition", "financial"]):
            return IntentPrediction(intent="scholarships", confidence=0.7, rationale=["Fallback: financial keywords"])
        elif any(word in text for word in ["study", "class", "exam", "homework", "grade", "professor"]):
            return IntentPrediction(intent="academics", confidence=0.7, rationale=["Fallback: academic keywords"])
        else:
            return IntentPrediction(intent="general", confidence=0.5, rationale=["Fallback: no clear keywords"])


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
        self._handoff_suggest_threshold = 0.5  # score that triggers a handoff suggestion (lowered for more suggestions)
        self._intent_suggestion_floor = 0.0  # classifier confidence that supports a suggestion

        self._switching_cues = [
            # generic switching
            "switch", "switch to", "change", "different", "someone else", "another", "handoff", "hand off",
            "connect me", "transfer me", "talk to", "speak to",
            # intents by topic
            "career help", "job", "jobs", "internship", "co-op", "resume", "interview",
            "stress", "mental health", "burnout", "wellness", "therapy", "counseling",
            "money", "funding", "scholarship", "grant", "aid", "financial",
            "club", "event", "workshop", "seminar", "hackathon",
            # goddess names
            "gaia", "athena", "aphrodite", "artemis", "tyche"
        ]

        # NEW: explicit name/verb detection (e.g., "switch to Athena", "Athena please")
        self._name_aliases = {
            "gaia": ["gaia"],
            "athena": ["athena"],
            "aphrodite": ["aphrodite"],
            "artemis": ["artemis"],
            "tyche": ["tyche"],
        }
        self._switch_verbs = [
            "switch", "change", "talk to", "connect", "handoff",
            "transfer", "route", "speak to", "chat with"
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

    async def get_response(self, user_id: str, message: str, db, preferred_goddess: Optional[str] = None) -> ChatResponse:
        user = await get_user(db, user_id)
        if not user:
            raise ValueError("User profile not found")

        # Use the tab the user is typing under, if provided; else fall back
        current_goddess = (preferred_goddess or user.selected_goddess or "gaia").lower()

        # If the user clicked into a different tab, remember it so subsequent messages align
        if preferred_goddess and preferred_goddess != user.selected_goddess:
            await update_user_goddess(
                db, user_id,
                goddess=current_goddess,
                quiz_results=user.quiz_results or {},
                suggested=None, handoff_stage=None, routing_state=None
            )

        # Clear any pending handoff if user sends a new message
        # This ensures we don't get stuck in text-based confirmation flows
        if user.handoff_stage == "awaiting_confirmation":
            await update_user_goddess(
                db, user_id, current_goddess,
                quiz_results=user.quiz_results or {},
                suggested=None, handoff_stage=None, routing_state=None
            )
            # Continue processing the new message normally

        # Classify intent using Gemini
        intent_prediction = await self._intent_classifier.predict(message)

        # Try explicit user choice first (e.g., "switch to Athena", "Athena please")
        explicit = self._parse_explicit_goddess(message)
        if explicit and explicit != current_goddess:
            match_result = MatchResult(
                goddess=explicit,
                # set at suggest threshold so UX always shows the inline confirm card
                confidence=self._handoff_suggest_threshold,
                rationale=[f"user explicitly asked for {explicit}"],
            )
            intent_conf = max(intent_prediction.confidence, 0.9)
        else:
            # Use Gemini's suggested goddess from intent classification
            suggested_goddess = intent_prediction.suggested_goddess
            if not suggested_goddess:
                # Fallback to matcher if Gemini didn't suggest a goddess
                match_result = self._matcher.match_for_message(message, intent_prediction.intent)
            else:
                match_result = MatchResult(
                    goddess=suggested_goddess,
                    confidence=intent_prediction.confidence,
                    rationale=intent_prediction.rationale,
                )
            intent_conf = intent_prediction.confidence

        decision = self._decide_routing(
            current_goddess, match_result, intent_conf, message
        )

        # (Optional but handy) log routing decisions while tuning
        LOGGER.info(
            "router_decision",
            extra={
                "user": user_id,
                "current": current_goddess,
                "suggested": match_result.goddess,
                "score": match_result.confidence,
                "intent": intent_prediction.intent,
                "intent_conf": intent_conf,
                "mode": decision["mode"],
            },
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
        # NO AUTO-SWITCHING: All switches must go through confirmation
        if decision["mode"] == "suggest" and suggested_goddess:
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
            "switched": False,  # NO AUTO-SWITCHING: Always False
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

    def _parse_explicit_goddess(self, text: str) -> Optional[str]:
        """Return a goddess key if the user explicitly asked for one."""
        t = (text or "").lower().strip()
        if not t:
            return None
        for g, aliases in self._name_aliases.items():
            name_hit = any(a in t for a in aliases)
            if not name_hit:
                continue
            # Strong signals like "switch to athena", "connect me to aphrodite"
            if any(v in t for v in self._switch_verbs):
                return g
            # Light signals like "athena please", "athena?"
            if t == g or t.startswith(g + " ") or t.endswith(" please") or t.endswith("?"):
                return g
        return None

    def _decide_routing(self, current: str, match_result: MatchResult, intent_confidence: float, message: str) -> dict:
        decision = {"mode": "stay", "target": current, "suggested": None}
        suggested = match_result.goddess
        if not suggested or suggested == current:
            return decision

        score = match_result.confidence or 0.0
        message_lower = message.lower()
        explicit_switch = any(cue in message_lower for cue in self._switching_cues)
        has_intent_signal = intent_confidence >= self._intent_suggestion_floor

        # Explicit user request for a switch should also require confirmation
        if explicit_switch and score >= self._handoff_suggest_threshold:
            decision.update({"mode": "suggest", "suggested": suggested})
            return decision

        # Otherwise, propose a handoff (show the inline confirm card) if confident enough
        if (score >= self._handoff_suggest_threshold) or has_intent_signal:
            decision.update({"mode": "suggest", "suggested": suggested})
            return decision

        return decision



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
            f"You are {current_name}. A student has asked for help that {suggested_name} is better suited to handle.\n"
            "Write under 150 words, stay warm, and keep a mentoring tone.\n"
            f"Explain that {suggested_name} ({suggested_tagline}) would be the best person to help with this, citing resources with [#] if you reference them.\n"
            f"Reasoning: {handoff_reason}.\n"
            f"Suggest connecting the student to {suggested_name} for better assistance.\n"
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
        rationale = routing_state.get("rationale") or []

        # Update user's selected goddess and clear handoff state
        await update_user_goddess(
            db, user_id, new_goddess,
            quiz_results=user.quiz_results or {},
            suggested=None, handoff_stage=None, routing_state=None
        )

        # Generate a welcome message from the new goddess without processing old message
        response_text = await self._generate_handoff_welcome(new_goddess)
        response_intent = "handoff_confirmed"

        await append_intents(db, user_id, [response_intent])
        await add_chat_message(
            db, user_id, role="assistant", content=response_text,
            goddess=new_goddess, intent=response_intent, citations=[]
        )

        trace = {
            "stage": None,
            "current_goddess": new_goddess,
            "previous_goddess": previous,
            "switched": True,
            "mode": "confirmed_handoff",
            "confirmed": True,
        }
        if rationale:
            trace["handoff_reason"] = rationale

        return ChatResponse(
            message=response_text,
            goddess=new_goddess,
            intent=response_intent,
            citations=[],
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
