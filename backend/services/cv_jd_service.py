from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, List
import re
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase


CLOUD_NATIVE_KEYWORDS = [
    "aws",
    "kubernetes",
    "k8s",
    "prometheus",
    "grafana",
    "terraform",
    "helm",
    "argocd",
    "ci/cd",
    "gitops",
    "service mesh",
    "observability",
    "sre",
    "incident response",
    "eks",
    "iam",
]


ROLE_KEYWORDS = [
    "cloud engineer",
    "devops engineer",
    "site reliability engineer",
    "platform engineer",
    "sre",
]


SENIORITY_KEYWORDS = ["junior", "mid", "senior", "staff", "principal", "lead"]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _decode_text(content: bytes, content_type: Optional[str]) -> str:
    if not content:
        return ""

    allowed_plain = {"text/plain", "text/markdown", "application/json"}
    if content_type in allowed_plain:
        return content.decode("utf-8", errors="ignore")

    return ""


def _extract_keyword_hits(text: str, keywords: List[str]) -> List[str]:
    normalized = text.lower()
    hits: List[str] = []
    for keyword in keywords:
        if keyword in normalized:
            hits.append(keyword)
    return hits


def _cloud_native_focus_score(text: str) -> float:
    if not text:
        return 0.0
    hits = _extract_keyword_hits(text, CLOUD_NATIVE_KEYWORDS)
    max_hits = max(1, len(CLOUD_NATIVE_KEYWORDS))
    return round(min(1.0, len(hits) / max_hits), 3)


def _extract_skills(text: str) -> List[str]:
    hits = _extract_keyword_hits(text, CLOUD_NATIVE_KEYWORDS)
    canonical = []
    seen = set()
    for item in hits:
        label = item.upper() if item in {"aws", "sre", "eks", "iam"} else item.title()
        if label not in seen:
            seen.add(label)
            canonical.append(label)
    return canonical


def _infer_role(text: str) -> Optional[str]:
    hits = _extract_keyword_hits(text, ROLE_KEYWORDS)
    if not hits:
        return None
    role = hits[0]
    if role == "sre":
        return "Site Reliability Engineer"
    return role.title()


def _infer_seniority(text: str) -> Optional[str]:
    hits = _extract_keyword_hits(text, SENIORITY_KEYWORDS)
    if not hits:
        return None
    return hits[0]


class CvJdService:
    async def ingest_cv(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        raw_text: Optional[str] = None,
    ) -> Dict:
        parsed_text = _normalize_text(raw_text or _decode_text(content, content_type))
        skills = _extract_skills(parsed_text)
        focus = _cloud_native_focus_score(parsed_text)

        document_id = f"cv_{uuid.uuid4().hex}"
        doc = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "content_type": content_type,
            "raw_text": parsed_text,
            "extracted_skills": skills,
            "cloud_native_focus_score": focus,
            "created_at": datetime.utcnow(),
        }
        await db.interviewer_v2_cv_docs.insert_one(doc)
        return doc

    async def ingest_job_description(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        raw_text: Optional[str] = None,
    ) -> Dict:
        parsed_text = _normalize_text(raw_text or _decode_text(content, content_type))
        must_have_skills = _extract_skills(parsed_text)
        focus = _cloud_native_focus_score(parsed_text)

        document_id = f"jd_{uuid.uuid4().hex}"
        doc = {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "content_type": content_type,
            "raw_text": parsed_text,
            "inferred_role": _infer_role(parsed_text),
            "inferred_seniority": _infer_seniority(parsed_text),
            "must_have_skills": must_have_skills,
            "cloud_native_focus_score": focus,
            "created_at": datetime.utcnow(),
        }
        await db.interviewer_v2_jd_docs.insert_one(doc)
        return doc


cv_jd_service = CvJdService()
