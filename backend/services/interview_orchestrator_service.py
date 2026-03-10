from __future__ import annotations

from datetime import datetime
from typing import Dict, List
import random
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase


DEFAULT_COMPETENCIES = [
    "Cloud Architecture",
    "Kubernetes Operations",
    "Observability and Monitoring",
    "CI/CD and Automation",
    "Security and Governance",
    "Incident Response",
]


QUESTION_BANK = {
    "Cloud Architecture": [
        "Design a multi-region cloud architecture for a customer-facing platform with strict uptime and latency goals. Explain your decisions for traffic routing, data consistency, failure isolation, and cost trade-offs.",
        "You are migrating a monolith into a globally distributed platform. Walk through your target multi-region architecture, failover model, data partitioning strategy, and how you balance reliability against spend.",
        "How would you architect a high-traffic SaaS application across regions to achieve low latency and high availability? Cover ingress routing, state management, disaster recovery, and cost controls.",
    ],
    "Kubernetes Operations": [
        "A production Kubernetes workload is repeatedly restarting and error budgets are burning. Walk through your triage plan, the signals you inspect first, likely root causes, and your stabilization strategy.",
        "Your cluster shows intermittent 5xx spikes after a deployment. Explain how you would investigate Kubernetes health, isolate the fault domain, and recover safely.",
    ],
    "Observability and Monitoring": [
        "Define an observability strategy for a critical service using metrics, logs, and traces. Specify practical SLIs/SLOs and alert rules that reduce noise while preserving incident detection speed.",
        "Build an observability design for a distributed API platform. What telemetry would you collect, how would alerts be tuned, and how would you shorten mean time to detect and resolve incidents?",
    ],
    "CI/CD and Automation": [
        "Design a CI/CD workflow that balances delivery speed with safety for a microservices platform. Include promotion gates, rollout strategy, rollback design, and controls for risky changes.",
        "How would you structure a delivery pipeline for dozens of services so teams can ship frequently without increasing change failure rate? Include test strategy, progressive rollout, and rollback automation.",
    ],
    "Security and Governance": [
        "Describe how you enforce security and governance in cloud-native delivery: IAM boundaries, secrets lifecycle, policy-as-code, and auditability across environments.",
        "Explain a practical security-by-default platform model for DevOps teams, including access control, secret handling, software supply chain checks, and compliance evidence collection.",
    ],
    "Incident Response": [
        "Describe your end-to-end incident response process for a Sev-1 outage, from first alert to recovery and post-incident learning. Emphasize communication and decision-making under pressure.",
        "A critical production service is degraded during peak traffic. Walk through your incident command approach, mitigation path, stakeholder communication, and post-incident hardening plan.",
    ],
}


SIGNAL_BANK = {
    "Cloud Architecture": ["multi-region routing", "rto/rpo", "failure domains", "auto scaling", "consistency trade-off", "cost controls"],
    "Kubernetes Operations": ["events and logs", "resource pressure", "readiness/liveness probes", "rollout history", "root cause validation", "safe remediation"],
    "Observability and Monitoring": ["sli/slo", "golden signals", "high-quality alerting", "trace correlation", "runbooks", "noise reduction"],
    "CI/CD and Automation": ["progressive delivery", "automated tests", "rollback strategy", "change approvals", "pipeline observability", "blast-radius control"],
    "Security and Governance": ["least privilege", "secrets rotation", "policy as code", "supply chain security", "audit trails", "compliance evidence"],
    "Incident Response": ["triage and severity", "stakeholder communication", "containment", "service restoration", "postmortem actions", "follow-up ownership"],
}


class InterviewOrchestratorService:
    async def generate_blueprint(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        cv_document_id: str,
        jd_document_id: str,
        target_duration_minutes: int,
        strict_mode: bool,
    ) -> Dict:
        cv_doc = await db.interviewer_v2_cv_docs.find_one({"document_id": cv_document_id, "user_id": user_id})
        jd_doc = await db.interviewer_v2_jd_docs.find_one({"document_id": jd_document_id, "user_id": user_id})

        if not cv_doc:
            raise ValueError("CV document not found")
        if not jd_doc:
            raise ValueError("Job description document not found")

        skills = set((cv_doc.get("extracted_skills") or []))
        must_have = set((jd_doc.get("must_have_skills") or []))

        prioritized_competencies = self._choose_competencies(skills, must_have, target_duration_minutes)
        latest_blueprint = await db.interviewer_v2_blueprints.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )

        previous_first_competency = None
        previous_first_question = None
        if latest_blueprint:
            previous_plan = latest_blueprint.get("question_plan") or []
            if previous_plan:
                previous_first_competency = previous_plan[0].get("competency")
                previous_first_question = previous_plan[0].get("question")

        question_plan = self._build_question_plan(
            prioritized_competencies,
            previous_first_competency=previous_first_competency,
            previous_first_question=previous_first_question,
        )

        blueprint_id = f"bp_{uuid.uuid4().hex}"
        blueprint = {
            "blueprint_id": blueprint_id,
            "user_id": user_id,
            "cv_document_id": cv_document_id,
            "jd_document_id": jd_document_id,
            "target_duration_minutes": target_duration_minutes,
            "strict_mode": strict_mode,
            "delivery_mode": "tts_interviewer_led",
            "competencies": prioritized_competencies,
            "question_plan": question_plan,
            "created_at": datetime.utcnow(),
        }
        await db.interviewer_v2_blueprints.insert_one(blueprint)
        return blueprint

    def _choose_competencies(self, skills: set, must_have: set, target_duration_minutes: int) -> List[str]:
        limit = 6 if target_duration_minutes >= 30 else 4
        selected = []

        if must_have:
            selected.extend([item for item in DEFAULT_COMPETENCIES if any(token in item.lower() for token in [s.lower() for s in must_have])])

        if not selected and skills:
            selected.extend([item for item in DEFAULT_COMPETENCIES if any(token in item.lower() for token in [s.lower() for s in skills])])

        if not selected:
            selected = list(DEFAULT_COMPETENCIES)

        deduped = []
        seen = set()
        for item in selected + DEFAULT_COMPETENCIES:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
            if len(deduped) >= limit:
                break

        return deduped

    def _build_question_plan(
        self,
        competencies: List[str],
        previous_first_competency: str | None = None,
        previous_first_question: str | None = None,
    ) -> List[Dict]:
        ordered_competencies = list(competencies or [])
        random.shuffle(ordered_competencies)

        if previous_first_competency and len(ordered_competencies) > 1 and ordered_competencies[0] == previous_first_competency:
            for idx, competency in enumerate(ordered_competencies[1:], start=1):
                if competency != previous_first_competency:
                    ordered_competencies[0], ordered_competencies[idx] = ordered_competencies[idx], ordered_competencies[0]
                    break

        plan: List[Dict] = []
        for idx, competency in enumerate(ordered_competencies):
            candidates = list(
                QUESTION_BANK.get(
                    competency,
                    ["Describe your practical approach for this competency in production systems."],
                )
            )

            if idx == 0 and previous_first_question and len(candidates) > 1:
                filtered = [question for question in candidates if question != previous_first_question]
                if filtered:
                    candidates = filtered

            plan.append(
                {
                    "competency": competency,
                    "question": random.choice(candidates),
                    "expected_signals": SIGNAL_BANK.get(competency, []),
                }
            )

        return plan


interview_orchestrator_service = InterviewOrchestratorService()
