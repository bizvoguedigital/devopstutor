# AI Interviewer v2 (CV + JD + Webcam) - Principal Engineer Implementation Blueprint

## 1) Scope Guardrails

This initiative is explicitly scoped to cloud-native interviewing.

- Platform domains: AWS, Kubernetes, Prometheus, Grafana, Terraform, Helm, ArgoCD, CI/CD, service mesh, observability, incident response.
- Out of scope for initial launch: non-technical personality scoring, face recognition, identity verification from webcam, and hiring recommendations without evidence.
- Product mode: coaching-first (candidate improvement), recruiter mode optional behind feature flag.
- Interviewer role lock: the AI always acts as interviewer, not a general assistant, during active sessions.
- Refusal behavior: any out-of-scope request is declined and redirected back to the current interview question.

## 2) Framework Evaluation (Decision)

### Orchestration
- **Chosen:** LangGraph
- Why: explicit state machine, checkpointing, retries, deterministic edge control for multi-turn interviews.
- Alternative considered: Haystack pipelines (simpler, but less control for adaptive turn-by-turn branching).

### Document Ingestion + Grounding
- **Chosen:** LlamaIndex + unstructured
- Why: strong ingestion connectors, metadata extraction, and flexible chunking for CV/JD grounding.

### Realtime AV
- **Chosen:** LiveKit (WebRTC under the hood)
- Why: production-ready media infra, lower ops burden versus self-managed SFU.

### STT/TTS
- STT: Faster-Whisper (primary)
- TTS: ElevenLabs (primary) with browser fallback already present

## 3) Target Architecture (v2)

### New Backend Services
- `backend/services/cv_jd_service.py`
  - Parse CV/JD (PDF/DOCX/text/url)
  - Extract structured profile and role rubric
- `backend/services/interview_orchestrator_service.py`
  - LangGraph interview state machine
  - Adaptive question planning + rubric coverage tracking
- `backend/services/rubric_service.py`
  - Cloud-native competency rubrics by role and level
- `backend/services/interview_policy_service.py`
  - Interview-mode policy checks
  - Prompt-injection / jailbreak detection
  - Standard refusal-and-redirect responses

### Data Collections (Mongo)
- `candidate_profiles`
  - `profile_id`, `user_id`, `source_doc_ids`, `skills`, `experience_summary`, `projects`, `certifications`
- `job_profiles`
  - `job_profile_id`, `user_id`, `title`, `must_have`, `nice_to_have`, `seniority`, `domain_focus`
- `interview_blueprints`
  - `blueprint_id`, `profile_id`, `job_profile_id`, `question_plan`, `rubric_map`, `target_duration_minutes`
- `interview_turns`
  - `session_id`, `turn_number`, `question`, `answer_transcript`, `evidence_refs`, `scores`, `follow_up_reason`

## 4) API Contract Draft (Phase 1)

- `POST /api/interviewer-v2/documents/cv`
- `POST /api/interviewer-v2/documents/job-description`
- `POST /api/interviewer-v2/blueprints/generate`
- `POST /api/interviewer-v2/sessions/start`
- `POST /api/interviewer-v2/sessions/{session_id}/turn`
- `GET /api/interviewer-v2/sessions/{session_id}/status`
- `POST /api/interviewer-v2/sessions/{session_id}/complete`

All scoring outputs must be JSON-schema constrained and include evidence references from transcript/CV/JD chunks.

During active sessions, user turn handling must run policy checks before orchestration:
- If policy fail: return refusal template + restate latest interview question
- If policy pass: continue normal interview turn processing

## 5) Rubric v1 (Cloud-Native Core)

Each domain scored 0-10 with evidence:

1. Cloud Architecture (AWS/K8s design decisions)
2. Reliability & SRE (SLO/SLI, alerting, incident handling)
3. Observability (Prometheus/Grafana/logging/tracing)
4. Delivery & Automation (CI/CD, GitOps, IaC)
5. Security & Governance (IAM, secrets, policy)
6. Communication & Trade-off Clarity

## 6) Milestones

### Sprint A (Start Now)
- Add DB schemas + API contracts + feature flags
- Implement CV/JD ingestion pipeline (no webcam yet)
- Generate first deterministic interview blueprint

### Sprint B
- Add adaptive turn orchestration and rubric coverage tracking
- Add transcript evidence linking and final scorecard

### Sprint C
- Add LiveKit webcam/mic session mode with consent flow
- Add optional communication analytics (non-biometric only)

## 7) Non-Functional Requirements

- p95 turn latency target: < 2.5s (text mode), < 4.0s (voice mode)
- Strong auditability: model version, prompt version, rubric version per turn
- Data governance: retention policies + delete by user/session
- Safety: no protected-attribute scoring, no opaque final recommendations
- Prompt security: enforce role immutability, anti-jailbreak filters, and refusal templates for non-interview asks

## 8) Immediate Engineering Backlog

1. Create `interviewer-v2` feature flag and config block
2. Add schema definitions for profile/job/blueprint/session-turn
3. Build CV/JD ingestion endpoint stubs with validation
4. Add blueprint generator service interface + placeholder implementation
5. Add evaluation JSON schema and validation utility
6. Add integration tests for ingestion and blueprint creation
7. Add interview policy middleware (context lock + refusal/redirect)
8. Add adversarial prompt test suite (role-switch, unrelated asks, jailbreak attempts)

## 9) Refusal Policy (v1)

When user asks unrelated questions, requests role switching, or attempts policy bypass:

1. Refuse briefly and politely
2. Re-anchor to interview context
3. Repeat or paraphrase the active interview question

Canonical response pattern:
- "I can’t help with that during this interview. Let’s stay focused."
- "Please answer the current question: <question_text>"
