from typing import List
import re


def estimate_communication_score(answer_text: str) -> float:
    text = (answer_text or "").strip()
    if not text:
        return 0.0

    words = [word for word in re.split(r"\s+", text) if word]
    word_count = len(words)
    sentence_count = max(1, len(re.findall(r"[.!?]", text)))
    avg_sentence_len = word_count / sentence_count

    depth_score = min(4.0, word_count / 30.0)
    structure_score = min(3.0, sentence_count * 0.75)
    clarity_penalty = 0.0 if avg_sentence_len <= 24 else min(2.0, (avg_sentence_len - 24) / 10.0)
    signal_bonus = 1.0 if any(token in text.lower() for token in ["because", "therefore", "trade-off", "monitor", "rollback"]) else 0.0

    score = 3.0 + depth_score + structure_score + signal_bonus - clarity_penalty
    return round(max(0.0, min(10.0, score)), 1)


def dimension_status(score: float, benchmark: float) -> str:
    if score >= benchmark + 0.5:
        return "above_benchmark"
    if score >= benchmark - 0.5:
        return "on_track"
    return "needs_improvement"


def extract_insight_phrases(values: List[str], fallback: List[str]) -> List[str]:
    phrases: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        first = re.split(r"(?<=[.!?])\s+", text)[0].strip()
        cleaned = re.sub(r"\s+", " ", first)
        if len(cleaned) < 24:
            continue
        phrases.append(cleaned)

    deduped: List[str] = []
    seen = set()
    for phrase in phrases:
        key = phrase.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(phrase)
        if len(deduped) >= 5:
            break

    if deduped:
        return deduped
    return fallback


def count_words(text: str) -> int:
    return len([word for word in re.split(r"\s+", (text or "").strip()) if word])
