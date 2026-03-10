import json
import uuid

import httpx


def main() -> int:
    base = "http://localhost:8000/api"
    uid = uuid.uuid4().hex[:8]
    email = f"smoke_{uid}@example.com"
    username = f"smoke_{uid}"
    password = "SmokePass123!"

    results = []

    def record(step: str, ok: bool, detail: str = "") -> None:
        results.append({"step": step, "ok": bool(ok), "detail": detail})

    with httpx.Client(base_url=base, timeout=60.0) as client:
        register = client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": "Smoke Test User",
            },
        )
        record("register", register.status_code == 200, f"status={register.status_code}")
        if register.status_code != 200:
            print(json.dumps(results, indent=2))
            return 1

        me = client.get("/auth/me")
        record("auth_me", me.status_code == 200, f"status={me.status_code}")
        if me.status_code != 200:
            print(json.dumps(results, indent=2))
            return 1

        cv_text = (
            "Principal DevOps engineer with multi-region AWS, Kubernetes, SRE, CI/CD, "
            "observability, security governance, incident response."
        )
        jd_text = (
            "Need principal cloud architect for resilient multi-region platform, strict uptime "
            "and latency, Kubernetes operations, observability and governance."
        )

        cv = client.post(
            "/interviewer-v2/documents/cv",
            files={"file": ("cv.txt", cv_text.encode("utf-8"), "text/plain")},
            data={"raw_text": cv_text},
        )
        record("upload_cv", cv.status_code == 200, f"status={cv.status_code}")
        if cv.status_code != 200:
            print(json.dumps(results, indent=2))
            print(cv.text)
            return 1

        jd = client.post(
            "/interviewer-v2/documents/job-description",
            files={"file": ("jd.txt", jd_text.encode("utf-8"), "text/plain")},
            data={"raw_text": jd_text},
        )
        record("upload_jd", jd.status_code == 200, f"status={jd.status_code}")
        if jd.status_code != 200:
            print(json.dumps(results, indent=2))
            print(jd.text)
            return 1

        blueprint = client.post(
            "/interviewer-v2/blueprints/generate",
            json={
                "cv_document_id": cv.json().get("document_id"),
                "jd_document_id": jd.json().get("document_id"),
                "target_duration_minutes": 20,
                "strict_mode": True,
            },
        )
        record("generate_blueprint", blueprint.status_code == 200, f"status={blueprint.status_code}")
        if blueprint.status_code != 200:
            print(json.dumps(results, indent=2))
            print(blueprint.text)
            return 1

        started = client.post(
            "/interviewer-v2/sessions/start",
            json={"blueprint_id": blueprint.json().get("blueprint_id")},
        )
        record("start_session", started.status_code == 200, f"status={started.status_code}")
        if started.status_code != 200:
            print(json.dumps(results, indent=2))
            print(started.text)
            return 1

        session_id = started.json().get("session_id")
        status = client.get(f"/interviewer-v2/sessions/{session_id}/status")
        record("session_status", status.status_code == 200, f"status={status.status_code}")

        answer = (
            "I would design active-active multi-region routing with health checks and latency-based "
            "traffic steering. I would define RTO and RPO, isolate failure domains, use autoscaling, "
            "and separate strong consistency for critical writes from eventual consistency for read-heavy "
            "flows. I would validate with game days, SLOs, incident drills, and cost controls for "
            "cross-region traffic."
        )
        turn = client.post(
            f"/interviewer-v2/sessions/{session_id}/turn",
            json={"user_response": answer},
        )
        record("submit_turn", turn.status_code == 200, f"status={turn.status_code}")

        complete = client.post(f"/interviewer-v2/sessions/{session_id}/complete")
        record("complete_session", complete.status_code == 200, f"status={complete.status_code}")
        if complete.status_code == 200:
            payload = complete.json()
            turn_reviews = payload.get("turn_reviews") or []
            record("summary_turn_reviews", isinstance(turn_reviews, list) and len(turn_reviews) > 0, f"count={len(turn_reviews)}")
            record("summary_score", isinstance(payload.get("average_score"), (int, float)), f"average_score={payload.get('average_score')}")

    print(json.dumps(results, indent=2))
    return 0 if all(item["ok"] for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
