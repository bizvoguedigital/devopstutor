from __future__ import annotations

from typing import Dict, Optional


DERAILMENT_PATTERNS = [
    "ignore previous",
    "ignore above",
    "jailbreak",
    "system prompt",
    "developer prompt",
    "act as",
    "roleplay",
    "tell me a joke",
    "weather",
    "movie",
    "politics",
    "write code for",
    "teach me",
    "how to answer",
    "give me the answer",
    "answer this for me",
    "can you answer",
    "what is your name",
    "who are you",
]


def _normalize_tokens(text: str):
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or ""))
    return [token for token in cleaned.split() if len(token) > 2]


class InterviewPolicyService:
    def evaluate_user_response(
        self,
        user_response: str,
        active_question: Optional[str],
        strict_mode: bool,
    ) -> Dict:
        text = (user_response or "").strip()

        if not text:
            return {
                "allowed": False,
                "reason": "empty_response",
                "message": self._refusal_message(active_question),
            }

        if strict_mode:
            lowered = text.lower()
            for pattern in DERAILMENT_PATTERNS:
                if pattern in lowered:
                    return {
                        "allowed": False,
                        "reason": "out_of_scope_or_role_switch_attempt",
                        "message": self._refusal_message(active_question),
                    }

            if active_question:
                question_tokens = set(_normalize_tokens(active_question))
                answer_tokens = _normalize_tokens(text)
                overlap = len(question_tokens.intersection(set(answer_tokens)))
                if len(answer_tokens) < 8 and overlap == 0:
                    return {
                        "allowed": False,
                        "reason": "response_too_brief_or_not_related_to_active_question",
                        "message": self._refusal_message(active_question),
                    }

        return {
            "allowed": True,
            "reason": None,
            "message": None,
        }

    @staticmethod
    def _refusal_message(active_question: Optional[str]) -> str:
        if active_question:
            return (
                "I can’t help with that during this interview. Let’s stay focused. "
                f"Please answer the current question: {active_question}"
            )
        return "I can’t help with that during this interview. Let’s stay focused."


interview_policy_service = InterviewPolicyService()
