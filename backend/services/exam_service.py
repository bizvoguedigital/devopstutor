import json
import re
from typing import Dict, List, Optional

from services.groq_service import GroqService


class ExamService:
    def __init__(self) -> None:
        self.groq_service = GroqService()

    def get_exam_duration_minutes(self, certificate: str) -> int:
        duration_map = {
            "AWS Cloud Practitioner": 90,
            "AWS Solutions Architect Associate": 130,
            "AWS Developer Associate": 130,
            "AWS SysOps Administrator Associate": 130,
            "AWS Solutions Architect Professional": 180,
            "AWS DevOps Engineer Professional": 180,
            "AWS Security Specialty": 170,
            "AWS Advanced Networking Specialty": 170,
            "AWS Machine Learning Specialty": 180,
            "AWS Data Analytics Specialty": 180,
            "AWS Database Specialty": 180,
            "AWS Data Engineer Associate": 130,
        }
        return duration_map.get(certificate, 130)

    def _get_category_profile(self, certificate: str) -> List[str]:
        profile_map = {
            "AWS Cloud Practitioner": ["cloud_concepts", "security", "technology", "billing"],
            "AWS Solutions Architect Associate": ["resilience", "performance", "security", "cost_optimization"],
            "AWS Developer Associate": ["development", "security", "deployment", "troubleshooting"],
            "AWS SysOps Administrator Associate": ["monitoring", "reliability", "deployment", "security"],
            "AWS Solutions Architect Professional": ["complex_architecture", "migration", "governance", "optimization"],
            "AWS DevOps Engineer Professional": ["cicd", "iac", "observability", "incident_response"],
            "AWS Security Specialty": ["identity", "detection", "infrastructure_security", "data_protection"],
            "AWS Advanced Networking Specialty": ["network_design", "hybrid_connectivity", "routing_dns", "network_security"],
            "AWS Machine Learning Specialty": ["data_engineering", "modeling", "training", "deployment_monitoring"],
            "AWS Data Analytics Specialty": ["ingestion", "storage", "processing", "visualization"],
            "AWS Database Specialty": ["database_design", "migration", "performance", "high_availability"],
            "AWS Data Engineer Associate": ["pipelines", "storage", "processing", "governance"],
        }
        return profile_map.get(certificate, ["compute", "storage", "networking", "security"])

    def _build_category_targets(self, question_count: int, categories: List[str]) -> Dict[str, int]:
        if not categories:
            return {"general": question_count}

        base = question_count // len(categories)
        remainder = question_count % len(categories)
        targets: Dict[str, int] = {}

        for idx, category in enumerate(categories):
            targets[category] = base + (1 if idx < remainder else 0)

        return {k: v for k, v in targets.items() if v > 0}

    async def generate_exam_questions(self, certificate: str, question_count: int) -> List[Dict]:
        questions_by_category: Dict[str, List[Dict]] = {}
        batch_size = 10
        seen_prompts = set()
        attempts = 0
        max_attempts = 8

        categories = self._get_category_profile(certificate)
        targets = self._build_category_targets(question_count, categories)

        for category in targets:
            questions_by_category[category] = []

        while attempts < max_attempts:
            remaining_total = sum(max(0, targets[c] - len(questions_by_category[c])) for c in targets)
            if remaining_total <= 0:
                break

            for category in targets:
                remaining = targets[category] - len(questions_by_category[category])
                if remaining <= 0:
                    continue

                batch_count = min(batch_size, remaining)
                batch_questions = await self._generate_question_batch(certificate, batch_count, category_hint=category)

                for item in batch_questions:
                    normalized = str(item.get("prompt", "")).strip().lower()
                    if not normalized or normalized in seen_prompts:
                        continue
                    seen_prompts.add(normalized)
                    questions_by_category[category].append(item)
                    if len(questions_by_category[category]) >= targets[category]:
                        break

            attempts += 1

        questions: List[Dict] = []
        for category in categories:
            questions.extend(questions_by_category.get(category, [])[: targets.get(category, 0)])

        if len(questions) < question_count:
            fallback_needed = question_count - len(questions)
            fallback_questions = await self._generate_question_batch(certificate, fallback_needed, category_hint=None)
            for item in fallback_questions:
                normalized = str(item.get("prompt", "")).strip().lower()
                if not normalized or normalized in seen_prompts:
                    continue
                seen_prompts.add(normalized)
                questions.append(item)
                if len(questions) >= question_count:
                    break

        return questions[:question_count]

    def _get_certificate_focus(self, certificate: str) -> str:
        focus_map = {
            "AWS Cloud Practitioner": "cloud concepts, billing and pricing, security basics, core services, support plans",
            "AWS Solutions Architect Associate": "design resilient architectures, high-performing architectures, secure applications, cost optimization",
            "AWS Developer Associate": "deployment, security, development with AWS services, refactoring, monitoring and troubleshooting",
            "AWS SysOps Administrator Associate": "monitoring and reporting, high availability, deployment and provisioning, storage and data management, security and compliance",
            "AWS Solutions Architect Professional": "complex multi-account design, migration, cost control, governance, network design, reliability",
            "AWS DevOps Engineer Professional": "SDLC automation, IaC, observability, incident response, security automation, governance",
            "AWS Security Specialty": "identity and access, detection and monitoring, infrastructure security, data protection, incident response",
            "AWS Advanced Networking Specialty": "network design, hybrid connectivity, routing, DNS, security, automation",
            "AWS Machine Learning Specialty": "data engineering, model development, training, deployment, monitoring",
            "AWS Data Analytics Specialty": "data ingestion, storage, processing, visualization, security",
            "AWS Database Specialty": "database design, migration, performance, availability, security",
            "AWS Data Engineer Associate": "data pipelines, storage, processing, governance, security",
        }
        return focus_map.get(certificate, "core services, security, networking, storage, compute")

    async def _generate_question_batch(self, certificate: str, batch_count: int, category_hint: Optional[str] = None) -> List[Dict]:
        focus = self._get_certificate_focus(certificate)
        category_pool = [
            "cloud_concepts",
            "security",
            "technology",
            "billing",
            "resilience",
            "performance",
            "cost_optimization",
            "development",
            "deployment",
            "troubleshooting",
            "monitoring",
            "reliability",
            "cicd",
            "iac",
            "observability",
            "incident_response",
            "identity",
            "infrastructure_security",
            "data_protection",
            "network_design",
            "hybrid_connectivity",
            "routing_dns",
            "network_security",
            "data_engineering",
            "modeling",
            "training",
            "deployment_monitoring",
            "ingestion",
            "storage",
            "processing",
            "visualization",
            "database_design",
            "migration",
            "high_availability",
            "pipelines",
            "governance",
            "compute",
            "networking",
            "automation",
        ]

        category_instruction = ""
        if category_hint:
            category_instruction = f"Focus this batch on category: {category_hint}."

        prompt = f"""Create {batch_count} ORIGINAL multiple-choice practice questions for the {certificate} exam.

Rules:
- Do NOT use or paraphrase real exam questions.
- Each question must have exactly 4 options labeled A, B, C, D.
- Provide the correct option letter and a 1-2 sentence explanation.
- Keep questions concise and exam-style.
    - Match the exam focus domains: {focus}.
{category_instruction}
- Use only these categories: {", ".join(category_pool)}.
- Avoid duplicating scenarios or phrasing within this batch.

Return ONLY valid JSON as an array of objects with this shape:
[
  {{
    "prompt": "question text",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_option": "A",
    "explanation": "why this is correct",
                        "category": "security|compute|storage|networking|billing|monitoring|serverless|databases|identity|automation"
  }}
]
"""

        response = await self.groq_service.generate_response(
            prompt=prompt,
            system_prompt=None,
            temperature=0.4
        )

        json_content = response
        if "```json" in response:
            json_content = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_content = response.split("```")[1].split("```")[0]

        json_match = re.search(r"\[[\s\S]*\]", json_content.strip())
        if json_match:
            json_content = json_match.group(0)

        parsed = []
        try:
            parsed = json.loads(json_content.strip())
        except Exception:
            object_blocks = re.findall(r"\{[\s\S]*?\}", json_content)
            recovered = []
            for block in object_blocks:
                try:
                    recovered.append(json.loads(block))
                except Exception:
                    continue
            parsed = recovered

        normalized = [self._normalize_question(item) for item in parsed if isinstance(item, dict)]
        return [item for item in normalized if item]

    def _normalize_question(self, item: Dict) -> Dict:
        prompt = str(item.get("prompt", "")).strip()
        options = item.get("options", [])
        if isinstance(options, dict):
            options = [
                f"A. {options.get('A', '')}",
                f"B. {options.get('B', '')}",
                f"C. {options.get('C', '')}",
                f"D. {options.get('D', '')}",
            ]
        elif isinstance(options, list):
            options = [str(opt).strip() for opt in options]

        options = [opt for opt in options if opt]
        if len(options) < 4 or not prompt:
            return None
        options = options[:4]

        correct_option = str(item.get("correct_option", "A")).strip().upper()
        if correct_option not in {"A", "B", "C", "D"}:
            correct_option = "A"

        explanation = str(item.get("explanation", "")).strip()
        category = str(item.get("category", "general")).strip().lower()

        return {
            "prompt": prompt,
            "options": options,
            "correct_option": correct_option,
            "explanation": explanation,
            "category": category,
        }


exam_service = ExamService()
