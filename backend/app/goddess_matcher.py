from __future__ import annotations

import logging
from functools import cached_property
from typing import Dict, List, Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - optional dependency during local dev
    SentenceTransformer = None  # type: ignore

from app.models import MatchResult

LOGGER = logging.getLogger(__name__)


class GoddessMatcher:
    """Rule-first matcher with optional embedding tie-breaker."""

    def __init__(self) -> None:
        self._config = self._load_config()
        self._persona_embeddings = self._build_persona_embeddings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def personas(self) -> Dict[str, Dict[str, str]]:
        return {
            key: {
                "id": key,
                "display_name": value["display_name"],
                "persona": value["persona"],
                "tagline": value["tagline"],
            }
            for key, value in self._config.items()
        }

    def persona_prompt(self, goddess: str) -> str:
        return self._config.get(goddess, {}).get("persona", "You are a helpful mentor.")

    def match_for_message(
        self,
        message: str,
        intent: Optional[str] = None,
    ) -> MatchResult:
        """Score each goddess using keyword heuristics and optional embeddings."""

        text = message.lower()
        scores: List[Tuple[str, float, List[str]]] = []

        for gid, data in self._config.items():
            rationale: List[str] = []
            base_score = 0.0

            for keyword in data["keywords"]:
                if keyword in text:
                    base_score += data["keyword_weight"]
                    rationale.append(f"matched keyword '{keyword}'")

            if intent:
                boost = data["intent_boost"].get(intent, 0.0)
                if boost:
                    base_score += boost
                    rationale.append(f"intent '{intent}' boost +{boost}")

            base_score += data.get("bias", 0.0)
            scores.append((gid, base_score, rationale))

        if not scores:
            return MatchResult(goddess="athena", confidence=0.0, rationale=["fallback to Athena"])

        scores.sort(key=lambda item: item[1], reverse=True)
        top_score = scores[0][1]
        candidates = [score for score in scores if score[1] == top_score]

        if len(candidates) > 1 and self._persona_embeddings:
            message_vector = self._encode_text(message)
            if message_vector is not None:
                best_gid = None
                best_similarity = -1.0
                for gid, _, rationale in candidates:
                    persona_vector = self._persona_embeddings.get(gid)
                    if persona_vector is None:
                        continue
                    similarity = float(message_vector @ persona_vector)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_gid = gid
                if best_gid:
                    chosen = next(score for score in scores if score[0] == best_gid)
                    rationale = list(chosen[2]) + ["embedding tie-breaker"]
                    return MatchResult(goddess=best_gid, confidence=chosen[1], rationale=rationale)

        chosen_gid, score, rationale = scores[0]
        return MatchResult(goddess=chosen_gid, confidence=score, rationale=rationale)

    def match_for_quiz(self, answers: List[int]) -> MatchResult:
        """Retain quiz support while aligning to config driven approach."""

        trait_totals = {trait: 0 for trait in self._trait_pool}
        for idx, value in enumerate(answers):
            trait = self._quiz_trait_map[idx % len(self._quiz_trait_map)]
            trait_totals[trait] += value

        best_gid = None
        best_score = -1.0
        rationale: List[str] = []
        for gid, data in self._config.items():
            score = 0.0
            debug: List[str] = []
            for trait, weight in data["trait_weights"].items():
                contribution = trait_totals.get(trait, 0) * weight
                if contribution:
                    debug.append(f"{trait}x{weight} -> {contribution}")
                score += contribution
            if score > best_score:
                best_score = score
                best_gid = gid
                rationale = debug

        assert best_gid is not None
        return MatchResult(goddess=best_gid, confidence=best_score, rationale=rationale)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _load_config() -> Dict[str, Dict]:
        return {
            "athena": {
                "display_name": "Athena",
                "tagline": "Strategic wisdom for academics and research.",
                "persona": (
                    "You are Athena, goddess of wisdom and strategy, a calm mentor who "
                    "guides NJIT scholars through coursework, research, and complex decisions. "
                    "Cite verifiable campus resources that back every recommendation."
                ),
                "keywords": [
                    "study", "exam", "class", "course", "research", "homework", "professor",
                    "grades", "tutoring", "academic", "library",
                ],
                "keyword_weight": 1.5,
                "intent_boost": {"academics": 3.0, "events": 0.5},
                "trait_weights": {"wisdom": 3, "strategy": 2, "independence": 1},
                "bias": 1.0,
            },
            "aphrodite": {
                "display_name": "Aphrodite",
                "tagline": "Well-being, community, and balance.",
                "persona": (
                    "You are Aphrodite, goddess of care and connection, helping students nurture "
                    "well-being, friendships, and a sustainable NJIT experience. "
                    "Offer accessible resources for wellness, counseling, and community."),
                "keywords": [
                    "stress", "wellness", "balance", "mental", "health", "friend", "community",
                    "counsel", "support group", "mindfulness", "self-care",
                ],
                "keyword_weight": 1.3,
                "intent_boost": {"wellbeing": 3.0, "events": 1.0},
                "trait_weights": {"nurturing": 3, "independence": 1},
                "bias": 0.8,
            },
            "hera": {
                "display_name": "Hera",
                "tagline": "Leadership, internships, and professional polish.",
                "persona": (
                    "You are Hera, goddess of leadership and resolve, championing professional "
                    "growth for NJIT students. Offer decisive guidance for internships, career "
                    "fairs, networking, and campus leadership programs."),
                "keywords": [
                    "career", "internship", "job", "resume", "interview", "co-op", "leadership",
                    "network", "handshake", "career fair", "professional",
                ],
                "keyword_weight": 1.4,
                "intent_boost": {"career": 3.0, "events": 1.5},
                "trait_weights": {"strategy": 2, "independence": 2, "wisdom": 1},
                "bias": 1.2,
            },
        }

    @property
    def _trait_pool(self) -> List[str]:
        traits = set()
        for config in self._config.values():
            traits.update(config["trait_weights"].keys())
        return sorted(list(traits))

    @cached_property
    def _quiz_trait_map(self) -> List[str]:
        return [
            "wisdom",
            "strategy",
            "independence",
            "nurturing",
            "leadership",
        ]

    def _build_persona_embeddings(self) -> Dict[str, object]:
        if not SentenceTransformer:
            LOGGER.warning("sentence-transformers not available; skipping embedding tie-breaker")
            return {}
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as exc:  # pragma: no cover - environmental failures
            LOGGER.warning("Could not load embedding model: %s", exc)
            return {}
        self._encoder_model = model
        embeddings: Dict[str, object] = {}
        for gid, data in self._config.items():
            vector = model.encode(data["persona"], normalize_embeddings=True)
            embeddings[gid] = vector
        return embeddings

    def _encode_text(self, text: str):
        model = getattr(self, "_encoder_model", None)
        if not model:
            return None
        try:
            return model.encode(text, normalize_embeddings=True)
        except Exception as exc:  # pragma: no cover - runtime guard
            LOGGER.debug("Embedding encoding failed: %s", exc)
            return None

