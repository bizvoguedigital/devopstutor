from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase


TURN_MIN_INTERVAL_SECONDS = 2


def _word_count(text: str) -> int:
    return len([token for token in (text or "").split() if token.strip()])


def _compute_turn_score(answer_text: str, expected_signals: List[str]) -> float:
    words = _word_count(answer_text)
    if words < 20:
        base = 2.0
    elif words < 60:
        base = 4.5
    elif words < 140:
        base = 6.0
    else:
        base = 6.8

    lowered = (answer_text or "").lower()
    matched = 0
    for signal in expected_signals or []:
        token = (signal or "").lower()
        if token and token in lowered:
            matched += 1

    signal_coverage = (matched / len(expected_signals)) if expected_signals else 0.0
    structure_tokens = ["first", "then", "because", "risk", "trade-off", "monitor", "rollback", "validate"]
    structure_hits = sum(1 for token in structure_tokens if token in lowered)
    structure_bonus = min(1.2, structure_hits * 0.2)
    coverage_bonus = min(2.0, signal_coverage * 2.0)
    signal_bonus = min(2.0, float(matched) * 0.5)

    return round(min(10.0, base + signal_bonus + coverage_bonus + structure_bonus), 1)


def _build_feedback(score: float) -> str:
    if score >= 8.0:
        return "Strong interview answer: clear structure, practical execution detail, and realistic trade-offs."
    if score >= 6.0:
        return "Good direction; strengthen with concrete production signals, explicit risks, and measurable validation steps."
    if score >= 4.0:
        return "Reasonable baseline; improve with deeper architecture rationale, operational safeguards, and fallback planning."
    return "Answer is too shallow; use a structured approach with diagnosis, decision criteria, implementation, and verification."


def _build_model_answer(competency: str, expected_signals: List[str]) -> str:
    normalized = (competency or "").strip().lower()

    templates: Dict[str, str] = {
        "cloud architecture": (
            "I would design this as an active-active multi-region architecture with clear failure isolation and explicit RTO/RPO targets. "
            "At the edge, I would use global traffic routing (for example latency-based routing with health checks) so users are sent to the nearest healthy region. "
            "For compute, I would run stateless services in each region behind regional load balancers with autoscaling based on CPU, request rate, and queue depth.\n\n"
            "For data, I would separate consistency requirements by domain: strongly consistent writes for critical transactions and eventual consistency for less critical or read-heavy features. "
            "I would use multi-region database patterns such as write-primary with cross-region replicas or sharded writes depending on business constraints, and I would define conflict-resolution rules up front. "
            "I would also isolate dependencies per failure domain (network, database, cache, and messaging) to prevent cascading failures.\n\n"
            "Operationally, I would define SLOs and monitor golden signals per region, run regular failover game days, and automate disaster recovery runbooks. "
            "Cost-wise, I would right-size baseline capacity, use autoscaling for peaks, and apply tiered storage plus cache strategies to reduce expensive cross-region traffic. "
            "Finally, I would validate this design with load tests, region-failure drills, and post-incident reviews to continuously improve resilience."
        ),
        "kubernetes operations": (
            "My first step is to stabilize impact and gather evidence before making broad changes. I would check pod events, restart reasons, and recent deployment history, "
            "then correlate with node-level metrics (memory pressure, CPU throttling, disk pressure, and network errors).\n\n"
            "I would inspect logs from both the application and sidecars, verify readiness/liveness/startup probes, and confirm resource requests/limits are realistic. "
            "Common causes include OOMKills, probe misconfiguration, dependency timeouts, bad rollouts, and secrets/config drift.\n\n"
            "For remediation, I would roll back unsafe releases quickly, patch probe thresholds, adjust resources, and apply targeted fixes behind safe rollout controls. "
            "Then I would validate recovery with error-rate and latency checks, and ensure no hidden saturation remains. "
            "After resolution, I would add preventive guardrails: canary checks, policy validations, and runbook updates for faster future triage."
        ),
        "observability and monitoring": (
            "I would start by defining SLIs and SLOs aligned to user outcomes, not just infrastructure metrics. "
            "For example: request success rate, p95/p99 latency, and service availability for critical endpoints.\n\n"
            "I would instrument metrics, logs, and traces with consistent correlation IDs so incidents can be investigated across layers. "
            "Alerting would prioritize actionable signals: burn-rate alerts for SLO violations, latency/error spikes, and saturation thresholds with anti-noise controls (grouping, inhibition, and deduplication).\n\n"
            "Each high-severity alert should map to a runbook with triage steps, probable causes, and rollback/mitigation options. "
            "I would continuously tune thresholds using incident retrospectives and false-positive analysis to keep alerts high quality and engineer-trust high."
        ),
        "ci/cd and automation": (
            "I would design CI/CD as a risk-managed pipeline: fast feedback in CI, controlled promotion in CD, and observable rollouts in production. "
            "CI would include unit/integration tests, static analysis, dependency and container scanning, and policy checks before artifacts are promoted.\n\n"
            "For CD, I would use progressive delivery (canary or blue/green), automated health gates, and instant rollback triggers based on error-rate and latency regression. "
            "High-risk services would require additional approval gates and tighter blast-radius limits.\n\n"
            "Operationally, I would make deployments auditable end-to-end with change metadata, deployment timelines, and clear ownership. "
            "The goal is high deployment frequency with low failure rate and fast recovery when incidents occur."
        ),
        "security and governance": (
            "I enforce security by embedding controls directly into platform workflows. "
            "Access is least-privilege by default using short-lived credentials and role boundaries, with regular entitlement reviews.\n\n"
            "Secrets are never stored in source control; they are managed through centralized secret stores with rotation policies, access auditing, and runtime injection. "
            "I apply policy-as-code to block noncompliant infrastructure and deployment changes before they reach production.\n\n"
            "For governance, I ensure continuous evidence collection: audit logs, config baselines, vulnerability posture, and exception approvals. "
            "This creates a repeatable security posture that supports both engineering velocity and compliance readiness."
        ),
        "incident response": (
            "For a Sev-1, I focus on fast coordination and controlled restoration. First, I confirm severity, establish an incident commander, assign roles, and open a communication channel with timestamps and clear ownership.\n\n"
            "I stabilize impact by identifying the most likely fault domain, applying safe mitigation (rollback, feature flag disablement, traffic shift), and monitoring customer impact continuously. "
            "Communication to stakeholders is frequent, factual, and time-boxed.\n\n"
            "After recovery, I run a blameless postmortem with timeline, root cause, contributing factors, and corrective actions with owners and due dates. "
            "I track follow-through on reliability improvements so incident learning translates into measurable risk reduction."
        ),
    }

    if normalized in templates:
        return templates[normalized]

    if not expected_signals:
        return (
            f"A strong answer for {competency} should include structure, trade-offs, operational considerations, and validation steps. "
            "Cover how you would diagnose, decide, implement, and measure success in production."
        )

    signals_text = ", ".join(expected_signals)
    return (
        f"A strong answer for {competency} can follow this structure: context and constraints, technical approach, risks and trade-offs, and validation. "
        f"Be sure to include these signals explicitly: {signals_text}. "
        "Close with how you would measure outcomes and improve the design over time."
    )


def _extract_signal_snippet(answer_text: str, signal: str) -> Optional[str]:
    text = (answer_text or "").strip()
    token = (signal or "").strip().lower()
    if not text or not token:
        return None

    lowered = text.lower()
    idx = lowered.find(token)
    if idx < 0:
        return None

    start = max(0, idx - 40)
    end = min(len(text), idx + len(signal) + 40)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def _build_evidence_refs(answer_text: str, expected_signals: List[str]) -> List[Dict]:
    evidence: List[Dict] = []
    for signal in expected_signals or []:
        snippet = _extract_signal_snippet(answer_text, signal)
        if snippet:
            evidence.append(
                {
                    "signal": signal,
                    "source": "candidate_response",
                    "snippet": snippet,
                }
            )
    return evidence


def _compute_competency_coverage(question_plan: List[Dict], turns: List[Dict]) -> Dict:
    coverage_map: Dict[str, Dict[str, object]] = {}

    for item in question_plan or []:
        competency = str(item.get("competency") or "General")
        expected = [str(signal) for signal in (item.get("expected_signals") or []) if str(signal).strip()]
        if competency not in coverage_map:
            coverage_map[competency] = {
                "expected": set(),
                "covered": set(),
                "scores": [],
                "answered_turns": 0,
            }
        for signal in expected:
            coverage_map[competency]["expected"].add(signal)

    for turn in turns or []:
        turn_number = int(turn.get("turn_number") or 0)
        if turn_number <= 0 or turn_number > len(question_plan):
            continue

        plan_item = question_plan[turn_number - 1]
        competency = str(plan_item.get("competency") or "General")
        if competency not in coverage_map:
            coverage_map[competency] = {
                "expected": set(),
                "covered": set(),
                "scores": [],
                "answered_turns": 0,
            }

        coverage_map[competency]["answered_turns"] = int(coverage_map[competency]["answered_turns"]) + 1
        turn_score = turn.get("score")
        if isinstance(turn_score, (int, float)):
            coverage_map[competency]["scores"].append(float(turn_score))

        expected_set = coverage_map[competency]["expected"]
        expected_lower = {signal.lower(): signal for signal in expected_set}

        for ref in turn.get("evidence_refs") or []:
            signal = str(ref.get("signal") or "").strip()
            if not signal:
                continue
            canonical = expected_lower.get(signal.lower(), signal)
            coverage_map[competency]["covered"].add(canonical)

    coverage_list: List[Dict] = []
    total_expected = 0
    total_covered = 0

    for competency, values in coverage_map.items():
        expected_signals = sorted(values["expected"])
        covered_signals = sorted(values["covered"])
        missed_signals = [signal for signal in expected_signals if signal not in values["covered"]]

        expected_count = len(expected_signals)
        covered_count = len([signal for signal in covered_signals if signal in values["expected"]])
        coverage_ratio = round((covered_count / expected_count), 3) if expected_count else 1.0
        scores = values.get("scores") or []
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        answered_turns = int(values.get("answered_turns") or 0)

        total_expected += expected_count
        total_covered += covered_count

        coverage_list.append(
            {
                "competency": competency,
                "expected_signals": expected_signals,
                "covered_signals": covered_signals,
                "missed_signals": missed_signals,
                "coverage_ratio": coverage_ratio,
                "answered_turns": answered_turns,
                "average_score": avg_score,
            }
        )

    coverage_list.sort(key=lambda item: item.get("competency", ""))
    overall_ratio = round((total_covered / total_expected), 3) if total_expected else 0.0

    return {
        "competency_coverage": coverage_list,
        "overall_signal_coverage_ratio": overall_ratio,
    }


def _build_strengths_and_focus(competency_coverage: List[Dict]) -> Dict:
    covered = [item for item in competency_coverage if int(item.get("answered_turns") or 0) > 0]

    strengths_sorted = sorted(
        covered,
        key=lambda item: (
            float(item.get("average_score") or 0.0),
            float(item.get("coverage_ratio") or 0.0),
            -len(item.get("missed_signals") or []),
        ),
        reverse=True,
    )

    focus_sorted = sorted(
        competency_coverage,
        key=lambda item: (
            float(item.get("coverage_ratio") or 0.0),
            float(item.get("average_score") or 0.0),
            -int(item.get("answered_turns") or 0),
        ),
    )

    top_strengths = [str(item.get("competency")) for item in strengths_sorted[:3] if item.get("competency")]
    improvement_focus = [
        str(item.get("competency"))
        for item in focus_sorted
        if item.get("competency") and (float(item.get("coverage_ratio") or 0.0) < 1.0 or int(item.get("answered_turns") or 0) == 0)
    ][:3]

    return {
        "top_strengths": top_strengths,
        "improvement_focus": improvement_focus,
    }


def _readiness_band(readiness_score: float) -> str:
    if readiness_score >= 7.5:
        return "interview_ready"
    if readiness_score >= 5.0:
        return "progressing"
    return "emerging"


class InterviewerV2SessionService:
    async def start_session(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        blueprint_id: str,
    ) -> Dict:
        blueprint = await db.interviewer_v2_blueprints.find_one(
            {"blueprint_id": blueprint_id, "user_id": user_id}
        )
        if not blueprint:
            raise ValueError("Interview blueprint not found")

        question_plan = blueprint.get("question_plan") or []
        if not question_plan:
            raise ValueError("Interview blueprint has no question plan")

        session_id = f"iv2s_{uuid.uuid4().hex}"
        now = datetime.utcnow()
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "blueprint_id": blueprint_id,
            "status": "active",
            "strict_mode": bool(blueprint.get("strict_mode", True)),
            "current_turn": 1,
            "total_turns": len(question_plan),
            "started_at": now,
            "updated_at": now,
            "completed_at": None,
        }
        await db.interviewer_v2_sessions.insert_one(session)

        return {
            **session,
            "current_question": question_plan[0].get("question"),
        }

    async def get_session_status(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_id: str,
    ) -> Dict:
        session = await db.interviewer_v2_sessions.find_one(
            {"session_id": session_id, "user_id": user_id}
        )
        if not session:
            raise ValueError("Interviewer-v2 session not found")

        blueprint = await db.interviewer_v2_blueprints.find_one(
            {"blueprint_id": session.get("blueprint_id"), "user_id": user_id}
        )
        if not blueprint:
            raise ValueError("Interview blueprint not found")

        question_plan = blueprint.get("question_plan") or []
        current_turn = int(session.get("current_turn", 1))
        current_question = None
        if session.get("status") == "active" and 1 <= current_turn <= len(question_plan):
            current_question = question_plan[current_turn - 1].get("question")

        recent_turn_docs = await db.interviewer_v2_turns.find(
            {"session_id": session_id, "user_id": user_id}
        ).sort("created_at", -1).limit(3).to_list(length=3)

        recent_evidence_refs: List[Dict] = []
        for turn in recent_turn_docs:
            for ref in turn.get("evidence_refs") or []:
                recent_evidence_refs.append(
                    {
                        "signal": str(ref.get("signal") or ""),
                        "source": str(ref.get("source") or "candidate_response"),
                        "snippet": str(ref.get("snippet") or ""),
                    }
                )

        scored_turns = await db.interviewer_v2_turns.find(
            {"session_id": session_id, "user_id": user_id, "refusal": False}
        ).to_list(length=None)
        coverage = _compute_competency_coverage(question_plan=question_plan, turns=scored_turns)

        return {
            "session_id": session.get("session_id"),
            "blueprint_id": session.get("blueprint_id"),
            "status": session.get("status"),
            "strict_mode": bool(session.get("strict_mode", True)),
            "current_turn": current_turn,
            "total_turns": int(session.get("total_turns", len(question_plan))),
            "current_question": current_question,
            "started_at": session.get("started_at"),
            "updated_at": session.get("updated_at"),
            "completed_at": session.get("completed_at"),
            "recent_evidence_refs": recent_evidence_refs,
            "competency_coverage": coverage["competency_coverage"],
            "overall_signal_coverage_ratio": coverage["overall_signal_coverage_ratio"],
        }

    async def submit_turn(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_id: str,
        user_response: str,
        policy_result: Dict,
    ) -> Dict:
        session = await db.interviewer_v2_sessions.find_one(
            {"session_id": session_id, "user_id": user_id}
        )
        if not session:
            raise ValueError("Interviewer-v2 session not found")

        if session.get("status") != "active":
            raise ValueError("Interviewer-v2 session is not active")

        blueprint = await db.interviewer_v2_blueprints.find_one(
            {"blueprint_id": session.get("blueprint_id"), "user_id": user_id}
        )
        if not blueprint:
            raise ValueError("Interview blueprint not found")

        question_plan = blueprint.get("question_plan") or []
        current_turn = int(session.get("current_turn", 1))
        if current_turn < 1 or current_turn > len(question_plan):
            raise ValueError("Invalid interviewer-v2 session turn state")

        current_plan_item = question_plan[current_turn - 1]
        active_question = current_plan_item.get("question", "")

        last_turn = await db.interviewer_v2_turns.find_one(
            {"session_id": session_id, "user_id": user_id},
            sort=[("created_at", -1)],
        )
        if last_turn and isinstance(last_turn.get("created_at"), datetime):
            elapsed_seconds = (datetime.utcnow() - last_turn.get("created_at")).total_seconds()
            if elapsed_seconds < TURN_MIN_INTERVAL_SECONDS:
                raise ValueError("Please wait a moment before submitting another response")

        if not policy_result.get("allowed"):
            refusal_message = policy_result.get("message") or "I can’t help with that during this interview. Let’s stay focused."
            now = datetime.utcnow()
            expected_signals = current_plan_item.get("expected_signals") or []
            await db.interviewer_v2_turns.insert_one(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "turn_number": current_turn,
                    "question": active_question,
                    "user_response": user_response,
                    "refusal": True,
                    "refusal_reason": policy_result.get("reason"),
                    "assistant_message": refusal_message,
                    "score": None,
                    "feedback": None,
                    "competency": current_plan_item.get("competency"),
                    "expected_signals": expected_signals,
                    "created_at": now,
                }
            )
            await db.interviewer_v2_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"updated_at": now}},
            )
            return {
                "session_id": session_id,
                "status": "active",
                "turn_number": current_turn,
                "refusal": True,
                "refusal_reason": policy_result.get("reason"),
                "assistant_message": refusal_message,
                "score": None,
                "feedback": None,
                "next_question": active_question,
                "completed": False,
            }

        expected_signals = current_plan_item.get("expected_signals") or []
        score = _compute_turn_score(user_response, expected_signals)
        feedback = _build_feedback(score)
        evidence_refs = _build_evidence_refs(user_response, expected_signals)

        next_turn = current_turn + 1
        completed = next_turn > len(question_plan)
        status = "completed" if completed else "active"
        next_question = None if completed else question_plan[next_turn - 1].get("question")

        assistant_message = (
            "Thank you. That concludes the interview. I will now generate your final assessment and coaching summary."
            if completed
            else f"Thanks. Next question: {next_question}"
        )

        now = datetime.utcnow()
        await db.interviewer_v2_turns.insert_one(
            {
                "session_id": session_id,
                "user_id": user_id,
                "turn_number": current_turn,
                "question": active_question,
                "user_response": user_response,
                "refusal": False,
                "refusal_reason": None,
                "assistant_message": assistant_message,
                "score": score,
                "feedback": feedback,
                "evidence_refs": evidence_refs,
                "competency": current_plan_item.get("competency"),
                "expected_signals": expected_signals,
                "created_at": now,
            }
        )

        await db.interviewer_v2_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "current_turn": next_turn if not completed else current_turn,
                    "status": status,
                    "updated_at": now,
                    "completed_at": now if completed else None,
                }
            },
        )

        return {
            "session_id": session_id,
            "status": status,
            "turn_number": current_turn,
            "refusal": False,
            "refusal_reason": None,
            "assistant_message": assistant_message,
            "score": score,
            "feedback": feedback,
            "next_question": next_question,
            "evidence_refs": evidence_refs,
            "completed": completed,
        }

    async def complete_session(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_id: str,
    ) -> Dict:
        session = await db.interviewer_v2_sessions.find_one(
            {"session_id": session_id, "user_id": user_id}
        )
        if not session:
            raise ValueError("Interviewer-v2 session not found")

        turns = await db.interviewer_v2_turns.find(
            {"session_id": session_id, "user_id": user_id, "refusal": False}
        ).to_list(length=None)
        all_turns = await db.interviewer_v2_turns.find(
            {"session_id": session_id, "user_id": user_id}
        ).to_list(length=None)

        blueprint = await db.interviewer_v2_blueprints.find_one(
            {"blueprint_id": session.get("blueprint_id"), "user_id": user_id}
        )
        if not blueprint:
            raise ValueError("Interview blueprint not found")
        question_plan = blueprint.get("question_plan") or []

        scored = [float(item.get("score")) for item in turns if isinstance(item.get("score"), (int, float))]
        avg = round(sum(scored) / len(scored), 2) if scored else 0.0

        evidence_refs: List[Dict] = []
        for turn in turns:
            for ref in turn.get("evidence_refs") or []:
                evidence_refs.append(
                    {
                        "signal": str(ref.get("signal") or ""),
                        "source": str(ref.get("source") or "candidate_response"),
                        "snippet": str(ref.get("snippet") or ""),
                    }
                )

        coverage = _compute_competency_coverage(question_plan=question_plan, turns=turns)
        ranking = _build_strengths_and_focus(coverage.get("competency_coverage") or [])
        overall_ratio = float(coverage.get("overall_signal_coverage_ratio") or 0.0)
        interview_readiness_score = round((avg * 0.7) + ((overall_ratio * 10.0) * 0.3), 2)
        readiness_band = _readiness_band(interview_readiness_score)

        turn_reviews: List[Dict] = []
        for turn in sorted(all_turns, key=lambda item: int(item.get("turn_number", 0))):
            turn_number = int(turn.get("turn_number") or 0)
            plan_item = question_plan[turn_number - 1] if 1 <= turn_number <= len(question_plan) else {}
            competency = str(turn.get("competency") or plan_item.get("competency") or "General")
            expected_signals = [str(signal) for signal in (turn.get("expected_signals") or plan_item.get("expected_signals") or []) if str(signal).strip()]
            is_refusal = bool(turn.get("refusal"))
            turn_reviews.append(
                {
                    "turn_number": turn_number,
                    "competency": competency,
                    "question": str(turn.get("question") or plan_item.get("question") or ""),
                    "user_response": str(turn.get("user_response") or ""),
                    "score": float(turn.get("score") or 0.0),
                    "feedback": str(
                        turn.get("feedback")
                        or turn.get("assistant_message")
                        or ("Response was out of scope for strict mode." if is_refusal else "")
                    ),
                    "model_answer": _build_model_answer(competency, expected_signals),
                }
            )

        completed_at = datetime.utcnow()
        await db.interviewer_v2_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "completed",
                    "updated_at": completed_at,
                    "completed_at": completed_at,
                }
            },
        )

        summary = (
            "Session completed with strong coverage across planned competencies."
            if avg >= 7.0
            else "Session completed. Focus on deeper technical signals and clearer trade-off reasoning next round."
        )

        session_artifact_id = f"iv2a_{uuid.uuid4().hex}"
        artifact_doc = {
            "session_artifact_id": session_artifact_id,
            "session_id": session_id,
            "blueprint_id": session.get("blueprint_id"),
            "user_id": user_id,
            "status": "completed",
            "turns_answered": len(turns),
            "average_score": avg,
            "overall_signal_coverage_ratio": coverage["overall_signal_coverage_ratio"],
            "interview_readiness_score": interview_readiness_score,
            "readiness_band": readiness_band,
            "top_strengths": ranking["top_strengths"],
            "improvement_focus": ranking["improvement_focus"],
            "competency_coverage": coverage["competency_coverage"],
            "turn_reviews": turn_reviews,
            "created_at": completed_at,
        }
        await db.interviewer_v2_session_artifacts.insert_one(artifact_doc)

        return {
            "session_id": session_id,
            "blueprint_id": session.get("blueprint_id"),
            "session_artifact_id": session_artifact_id,
            "status": "completed",
            "turns_answered": len(turns),
            "average_score": avg,
            "completed_at": completed_at,
            "summary": summary,
            "evidence_refs": evidence_refs,
            "competency_coverage": coverage["competency_coverage"],
            "overall_signal_coverage_ratio": coverage["overall_signal_coverage_ratio"],
            "interview_readiness_score": interview_readiness_score,
            "readiness_band": readiness_band,
            "top_strengths": ranking["top_strengths"],
            "improvement_focus": ranking["improvement_focus"],
            "turn_reviews": turn_reviews,
        }

    async def get_session_artifact(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_id: str,
    ) -> Dict:
        artifact = await db.interviewer_v2_session_artifacts.find_one(
            {"session_id": session_id, "user_id": user_id},
            sort=[("created_at", -1)],
        )
        if not artifact:
            raise ValueError("Interviewer-v2 session artifact not found")

        return {
            "session_artifact_id": artifact.get("session_artifact_id"),
            "session_id": artifact.get("session_id"),
            "blueprint_id": artifact.get("blueprint_id"),
            "status": artifact.get("status", "completed"),
            "turns_answered": int(artifact.get("turns_answered", 0)),
            "average_score": float(artifact.get("average_score", 0.0)),
            "overall_signal_coverage_ratio": float(artifact.get("overall_signal_coverage_ratio", 0.0)),
            "interview_readiness_score": float(artifact.get("interview_readiness_score", 0.0)),
            "readiness_band": artifact.get("readiness_band", "emerging"),
            "top_strengths": list(artifact.get("top_strengths") or []),
            "improvement_focus": list(artifact.get("improvement_focus") or []),
            "competency_coverage": list(artifact.get("competency_coverage") or []),
            "created_at": artifact.get("created_at"),
        }

    async def get_artifact_by_id(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_artifact_id: str,
    ) -> Dict:
        artifact = await db.interviewer_v2_session_artifacts.find_one(
            {"session_artifact_id": session_artifact_id, "user_id": user_id}
        )
        if not artifact:
            raise ValueError("Interviewer-v2 artifact not found")

        return {
            "session_artifact_id": artifact.get("session_artifact_id"),
            "session_id": artifact.get("session_id"),
            "blueprint_id": artifact.get("blueprint_id"),
            "status": artifact.get("status", "completed"),
            "turns_answered": int(artifact.get("turns_answered", 0)),
            "average_score": float(artifact.get("average_score", 0.0)),
            "overall_signal_coverage_ratio": float(artifact.get("overall_signal_coverage_ratio", 0.0)),
            "interview_readiness_score": float(artifact.get("interview_readiness_score", 0.0)),
            "readiness_band": artifact.get("readiness_band", "emerging"),
            "top_strengths": list(artifact.get("top_strengths") or []),
            "improvement_focus": list(artifact.get("improvement_focus") or []),
            "competency_coverage": list(artifact.get("competency_coverage") or []),
            "created_at": artifact.get("created_at"),
        }

    async def list_artifacts(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        readiness_band: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict:
        safe_limit = max(1, min(int(limit), 100))
        safe_offset = max(0, int(offset))
        allowed_sort_by = {"created_at", "average_score", "interview_readiness_score"}
        if sort_by not in allowed_sort_by:
            raise ValueError("Invalid sort_by. Allowed values: created_at, average_score, interview_readiness_score")

        allowed_sort_order = {"asc", "desc"}
        if sort_order not in allowed_sort_order:
            raise ValueError("Invalid sort_order. Allowed values: asc, desc")

        query: Dict[str, object] = {"user_id": user_id}
        status_filter = (status or "").strip()
        readiness_filter = (readiness_band or "").strip()
        if status_filter:
            query["status"] = status_filter
        if readiness_filter:
            query["readiness_band"] = readiness_filter

        direction = 1 if sort_order == "asc" else -1

        total = await db.interviewer_v2_session_artifacts.count_documents(query)
        docs = await db.interviewer_v2_session_artifacts.find(
            query
        ).sort(sort_by, direction).skip(safe_offset).limit(safe_limit).to_list(length=safe_limit)

        items: List[Dict] = []
        for artifact in docs:
            items.append(
                {
                    "session_artifact_id": artifact.get("session_artifact_id"),
                    "session_id": artifact.get("session_id"),
                    "blueprint_id": artifact.get("blueprint_id"),
                    "status": artifact.get("status", "completed"),
                    "turns_answered": int(artifact.get("turns_answered", 0)),
                    "average_score": float(artifact.get("average_score", 0.0)),
                    "overall_signal_coverage_ratio": float(artifact.get("overall_signal_coverage_ratio", 0.0)),
                    "interview_readiness_score": float(artifact.get("interview_readiness_score", 0.0)),
                    "readiness_band": artifact.get("readiness_band", "emerging"),
                    "top_strengths": list(artifact.get("top_strengths") or []),
                    "improvement_focus": list(artifact.get("improvement_focus") or []),
                    "competency_coverage": list(artifact.get("competency_coverage") or []),
                    "created_at": artifact.get("created_at"),
                }
            )

        return {
            "items": items,
            "total": int(total),
            "limit": safe_limit,
            "offset": safe_offset,
            "has_more": (safe_offset + len(items)) < int(total),
            "status_filter": status_filter or None,
            "readiness_band_filter": readiness_filter or None,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

    async def delete_artifact_by_id(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        session_artifact_id: str,
    ) -> Dict:
        existing = await db.interviewer_v2_session_artifacts.find_one(
            {"session_artifact_id": session_artifact_id, "user_id": user_id},
            projection={"_id": 1},
        )
        if not existing:
            raise ValueError("Interviewer-v2 artifact not found")

        result = await db.interviewer_v2_session_artifacts.delete_one(
            {"session_artifact_id": session_artifact_id, "user_id": user_id}
        )
        deleted = int(result.deleted_count or 0) > 0
        return {
            "session_artifact_id": session_artifact_id,
            "deleted": deleted,
            "message": "Artifact deleted" if deleted else "Artifact was not deleted",
        }

    async def cleanup_artifacts(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        keep_latest: int = 10,
        dry_run: bool = False,
    ) -> Dict:
        safe_keep = max(0, min(int(keep_latest), 1000))
        docs = await db.interviewer_v2_session_artifacts.find(
            {"user_id": user_id},
            projection={"session_artifact_id": 1},
        ).sort("created_at", -1).to_list(length=None)

        total_before = len(docs)
        if total_before <= safe_keep:
            return {
                "total_before": total_before,
                "keep_latest": safe_keep,
                "dry_run": dry_run,
                "removed_count": 0,
                "kept_count": total_before,
                "removed_artifact_ids": [],
            }

        remove_docs = docs[safe_keep:]
        remove_ids = [str(item.get("session_artifact_id") or "") for item in remove_docs if item.get("session_artifact_id")]

        removed_count = len(remove_ids)
        if not dry_run and remove_ids:
            result = await db.interviewer_v2_session_artifacts.delete_many(
                {"user_id": user_id, "session_artifact_id": {"$in": remove_ids}}
            )
            removed_count = int(result.deleted_count or 0)

        kept_count = total_before if dry_run else max(0, total_before - removed_count)
        return {
            "total_before": total_before,
            "keep_latest": safe_keep,
            "dry_run": dry_run,
            "removed_count": removed_count,
            "kept_count": kept_count,
            "removed_artifact_ids": remove_ids,
        }


interviewer_v2_session_service = InterviewerV2SessionService()
