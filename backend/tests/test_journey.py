"""Hành trình đầy đủ: tư vấn ẩn danh → đăng ký → đặt lịch → bác sĩ khám với Copilot → duyệt kế hoạch → theo dõi."""

from datetime import date, timedelta

from tests.conftest import API, register_and_login, say, start_consultation


def _patient_with_booking(client, message="Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú", email="lan@test.vn"):
    cid, headers = start_consultation(client)
    say(client, cid, headers, message)
    auth = register_and_login(client, email, consultation_id=cid, consultation_token=headers["X-Consult-Token"])
    r = client.post(
        f"{API}/appointments",
        json={"service_code": "breast_screening", "preferred_date": date.today().isoformat(), "consultation_id": cid},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    return auth, r.json()


def test_full_journey(client, doctor):
    patient, appt = _patient_with_booking(client)
    assert appt["priority"] == "routine" and appt["reason"]

    queue = client.get(f"{API}/doctor/appointments?status=requested", headers=doctor).json()
    assert queue["total"] == 1
    confirmed = client.post(
        f"{API}/doctor/appointments/{appt['id']}/confirm",
        json={"scheduled_date": date.today().isoformat()},
        headers=doctor,
    )
    assert confirmed.json()["status"] == "confirmed"

    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    brief = enc["brief"]
    assert brief and brief["draft_plan"] and brief["guideline_suggestions"]
    record = client.get(f"{API}/doctor/patients/{enc['patient_id']}/record", headers=doctor).json()
    event_ids = {e["id"] for e in record["timeline"]}
    assert {i for f in brief["key_facts"] for i in f["event_ids"]} <= event_ids
    # start là idempotent
    assert client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()["id"] == enc["id"]

    # Bệnh nhân chưa thấy gì trước khi bác sĩ kết thúc khám
    as_patient = client.get(f"{API}/encounters/{enc['id']}", headers=patient).json()
    assert as_patient["brief"] is None and as_patient["draft_plan"] is None and as_patient["final_plan"] is None
    assert as_patient["conclusion"] is None and as_patient["clinical_notes"] is None

    qa = client.post(
        f"{API}/doctor/encounters/{enc['id']}/copilot",
        json={"question": "Guideline nhũ ảnh áp dụng cho bệnh nhân này thế nào?", "history": []},
        headers=doctor,
    ).json()
    assert qa["sources"]

    plan = enc["draft_plan"]
    due = (date.today() + timedelta(days=30)).isoformat()
    plan["items"][0]["next_due"] = due
    done = client.post(
        f"{API}/doctor/encounters/{enc['id']}/finalize",
        json={
            "conclusion": "Khám vú chưa ghi nhận bất thường. Hẹn chụp nhũ ảnh.",
            "clinical_notes": "note nội bộ",
            "final_plan": plan,
        },
        headers=doctor,
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "finalized" and len(done.json()["reminders"]) == 1

    as_patient = client.get(f"{API}/encounters/{enc['id']}", headers=patient).json()
    assert as_patient["final_plan"]["items"] and as_patient["conclusion"]
    assert as_patient["brief"] is None and as_patient["clinical_notes"] is None

    record = client.get(f"{API}/patients/me/record", headers=patient).json()
    kinds = [e["kind"] for e in record["timeline"]]
    assert {
        "consult.summary",
        "appointment.requested",
        "appointment.confirmed",
        "encounter.started",
        "encounter.finalized",
    } <= set(kinds)
    assert record["appointments"][0]["status"] == "completed"

    answer = client.post(
        f"{API}/encounters/{enc['id']}/questions", json={"question": "Kế hoạch gồm gì?"}, headers=patient
    )
    assert answer.status_code == 200 and answer.json()["sources"]

    reminder = client.get(f"{API}/reminders", headers=patient).json()[0]
    assert (
        client.post(f"{API}/reminders/{reminder['id']}/complete", json={}, headers=patient).json()["status"] == "done"
    )
    assert len(client.get(f"{API}/reminders", headers=patient).json()) == 2

    metrics = client.get(f"{API}/doctor/metrics", headers=doctor).json()
    assert metrics["consultations"] == 1 and metrics["linked_consultations"] == 1
    assert metrics["encounters_finalized"] == 1 and metrics["plans_edited_by_doctor"] == 1
    runs = client.get(f"{API}/doctor/agent-runs", headers=doctor).json()
    assert {r["agent"] for r in runs["items"]} == {"navigator", "copilot", "copilot_qa", "patient_qa"}
    assert all(r["events"] or r["agent"] == "patient_qa" for r in runs["items"])


def test_red_flag_consultation_books_urgent_and_brief_has_no_plan(client, doctor):
    patient, appt = _patient_with_booking(client, "Tôi nữ 50 tuổi, đi ngoài ra máu 2 tuần nay", "an@test.vn")
    assert appt["priority"] == "urgent"
    _, routine = _patient_with_booking(client, "Tôi là nữ 45 tuổi", "binh@test.vn")
    queue = client.get(f"{API}/doctor/appointments", headers=doctor).json()["items"]
    assert queue[0]["id"] == appt["id"]  # ưu tiên khẩn lên đầu
    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    assert enc["brief"]["red_flags"] and enc["draft_plan"] is None


def test_finalize_rules(client, doctor):
    patient, appt = _patient_with_booking(client)
    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    url = f"{API}/doctor/encounters/{enc['id']}/finalize"
    assert client.post(url, json={"conclusion": " "}, headers=doctor).status_code == 422
    bad = enc["draft_plan"]
    bad["items"][0]["rationale"] = "Bạn bị ung thư vú."
    assert client.post(url, json={"conclusion": "ok", "final_plan": bad}, headers=doctor).status_code == 400
    assert client.post(url, json={"conclusion": "ok"}, headers=patient).status_code == 403
    no_plan = client.post(url, json={"conclusion": "Chưa cần tầm soát định kỳ.", "final_plan": None}, headers=doctor)
    assert no_plan.status_code == 200 and no_plan.json()["final_plan"] is None and no_plan.json()["reminders"] == []
    assert client.post(url, json={"conclusion": "lần hai"}, headers=doctor).status_code == 409
    assert client.post(f"{API}/doctor/encounters/{enc['id']}/brief", headers=doctor).status_code == 409


def test_patient_isolation(client, doctor):
    patient, appt = _patient_with_booking(client)
    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    other = register_and_login(client, "other@test.vn")
    assert client.get(f"{API}/encounters/{enc['id']}", headers=other).status_code == 404
    assert client.post(f"{API}/appointments/{appt['id']}/cancel", headers=other).status_code == 404
    assert client.get(f"{API}/doctor/appointments", headers=patient).status_code == 403
    assert client.get(f"{API}/doctor/patients/{enc['patient_id']}/record", headers=other).status_code == 403
    assert (
        client.post(f"{API}/encounters/{enc['id']}/questions", json={"question": "?"}, headers=patient).status_code
        == 409
    )


def test_booking_validation(client):
    auth = register_and_login(client, "v@test.vn")
    today = date.today()
    bad_service = {"service_code": "nope", "preferred_date": today.isoformat()}
    assert client.post(f"{API}/appointments", json=bad_service, headers=auth).status_code == 400
    past = {"service_code": "general_screening", "preferred_date": (today - timedelta(days=1)).isoformat()}
    assert client.post(f"{API}/appointments", json=past, headers=auth).status_code == 400
    ok = {"service_code": "general_screening", "preferred_date": today.isoformat()}
    ids = [client.post(f"{API}/appointments", json=ok, headers=auth).json()["id"] for _ in range(3)]
    assert client.post(f"{API}/appointments", json=ok, headers=auth).status_code == 409
    assert client.post(f"{API}/appointments/{ids[0]}/cancel", headers=auth).json()["status"] == "cancelled"
    assert client.post(f"{API}/appointments/{ids[0]}/cancel", headers=auth).status_code == 409


def _started_encounter(client, doctor, email="lan@test.vn"):
    patient, appt = _patient_with_booking(client, email=email)
    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    return patient, appt, enc


def _audit_actions(action: str) -> list:
    from app.database import SessionLocal
    from app.models import AuditLog

    with SessionLocal() as db:
        return db.query(AuditLog).filter(AuditLog.action == action).all()


def test_red_flag_after_booking_escalates_open_appointment(client, doctor):
    """R2: dấu hiệu cảnh báo xuất hiện SAU khi đặt lịch từ cùng phiên → lịch đang mở chuyển sang khẩn."""
    patient, appt = _patient_with_booking(client)
    assert appt["priority"] == "routine"
    reply = say(client, appt["consultation_id"], patient, "Em sờ thấy khối cứng ở vú")["last_reply"]
    assert reply["next_action"] == "urgent_care"
    queue = client.get(f"{API}/doctor/appointments", headers=doctor).json()["items"]
    assert [(a["id"], a["priority"]) for a in queue] == [(appt["id"], "urgent")]
    kinds = {e["kind"] for e in client.get(f"{API}/patients/me/record", headers=patient).json()["timeline"]}
    assert "appointment.escalated" in kinds


def test_edited_plan_guardrail_covers_method_and_sources(client, doctor):
    _, _, enc = _started_encounter(client, doctor)
    url = f"{API}/doctor/encounters/{enc['id']}/finalize"
    diag = enc["draft_plan"]
    diag["items"][0]["method"] = "Nhũ ảnh — bệnh nhân đã mắc ung thư vú"
    r = client.post(url, json={"conclusion": "ok", "final_plan": diag}, headers=doctor)
    assert r.status_code == 400 and "method" in r.json()["detail"]
    fake = client.get(f"{API}/doctor/encounters/{enc['id']}", headers=doctor).json()["draft_plan"]
    fake["items"][0]["sources"] = [{"doc_id": "made-up", "title": "x", "excerpt": "y"}]
    r = client.post(url, json={"conclusion": "ok", "final_plan": fake}, headers=doctor)
    assert r.status_code == 400 and "kho guideline" in r.json()["detail"]


def test_cannot_cancel_appointment_once_encounter_started(client, doctor):
    patient, appt, enc = _started_encounter(client, doctor)
    assert client.post(f"{API}/appointments/{appt['id']}/cancel", headers=patient).status_code == 409
    done = client.post(f"{API}/doctor/encounters/{enc['id']}/finalize", json={"conclusion": "ok"}, headers=doctor)
    assert done.status_code == 200
    assert client.get(f"{API}/appointments", headers=patient).json()[0]["status"] == "completed"


def test_finalize_requires_confirmed_appointment(client, doctor):
    from app.database import SessionLocal
    from app.models import Appointment

    _, appt, enc = _started_encounter(client, doctor)
    with SessionLocal() as db:  # trạng thái không nhất quán (dữ liệu cũ / sửa tay)
        db.get(Appointment, appt["id"]).status = "cancelled"
        db.commit()
    r = client.post(f"{API}/doctor/encounters/{enc['id']}/finalize", json={"conclusion": "ok"}, headers=doctor)
    assert r.status_code == 409
    assert client.get(f"{API}/doctor/encounters/{enc['id']}", headers=doctor).json()["status"] == "in_progress"


def test_only_starting_doctor_can_regenerate_or_finalize(client, doctor):
    _, _, enc = _started_encounter(client, doctor)
    other = register_and_login(client, "doc2@test.vn", "doctor")
    assert client.post(f"{API}/doctor/encounters/{enc['id']}/brief", headers=other).status_code == 403
    url = f"{API}/doctor/encounters/{enc['id']}/finalize"
    assert client.post(url, json={"conclusion": "ok"}, headers=other).status_code == 403
    done = client.post(url, json={"conclusion": "ok"}, headers=doctor)
    assert done.status_code == 200 and done.json()["doctor"]["email"] == "doc@test.vn"


def test_discarding_draft_is_audited_but_unchanged_draft_is_not(client, doctor):
    _, _, enc = _started_encounter(client, doctor)
    r = client.post(
        f"{API}/doctor/encounters/{enc['id']}/finalize", json={"conclusion": "ok", "use_draft": False}, headers=doctor
    )
    assert r.status_code == 200 and r.json()["final_plan"] is None
    [audit] = _audit_actions("plan.edit")
    assert audit.before == enc["draft_plan"] and audit.after is None
    assert client.get(f"{API}/doctor/metrics", headers=doctor).json()["plans_edited_by_doctor"] == 1

    _, _, kept = _started_encounter(client, doctor, email="kept@test.vn")
    r = client.post(f"{API}/doctor/encounters/{kept['id']}/finalize", json={"conclusion": "ok"}, headers=doctor)
    assert r.status_code == 200 and r.json()["final_plan"] == kept["draft_plan"]
    assert len(_audit_actions("plan.edit")) == 1  # duyệt nguyên bản nháp không phải là sửa


def test_interval_cap_and_next_cycle_overflow_is_safe(client, doctor):
    from app.database import SessionLocal
    from app.models import Encounter

    patient, _, enc = _started_encounter(client, doctor)
    url = f"{API}/doctor/encounters/{enc['id']}/finalize"
    plan = enc["draft_plan"]
    plan["items"][0]["next_due"] = date.today().isoformat()
    plan["items"][0]["interval_months"] = 1_000_000
    assert client.post(url, json={"conclusion": "ok", "final_plan": plan}, headers=doctor).status_code == 422
    plan["items"][0]["interval_months"] = 12
    assert client.post(url, json={"conclusion": "ok", "final_plan": plan}, headers=doctor).status_code == 200
    with SessionLocal() as db:  # dữ liệu cũ (trước khi có giới hạn) với chu kỳ vượt phạm vi lịch
        e = db.get(Encounter, enc["id"])
        e.final_plan = {**e.final_plan, "items": [{**e.final_plan["items"][0], "interval_months": 1_000_000}]}
        db.commit()
    reminder = client.get(f"{API}/reminders", headers=patient).json()[0]
    r = client.post(f"{API}/reminders/{reminder['id']}/complete", json={}, headers=patient)
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert len(client.get(f"{API}/reminders", headers=patient).json()) == 1  # không sinh chu kỳ kế tiếp


def test_patient_question_never_returns_trace(client, doctor, monkeypatch):
    from ai_core.schemas import QuestionAnswer

    from app.services import agent_service

    patient, _, enc = _started_encounter(client, doctor)
    client.post(f"{API}/doctor/encounters/{enc['id']}/finalize", json={"conclusion": "ok"}, headers=doctor)

    async def answer_with_trace(question, plan):
        return QuestionAnswer(
            answer="a", disclaimer="d", trace_id="t", trace_events=[{"node": "respond", "status": "ok"}]
        )

    monkeypatch.setattr(agent_service, "answer_question", answer_with_trace)
    r = client.post(f"{API}/encounters/{enc['id']}/questions", json={"question": "Kế hoạch gồm gì?"}, headers=patient)
    assert r.status_code == 200 and r.json()["trace_events"] == []
    runs = client.get(f"{API}/doctor/agent-runs?agent=patient_qa", headers=doctor).json()["items"]
    assert runs[0]["events"] == [{"node": "respond", "status": "ok"}]  # trace vẫn lưu cho bác sĩ


def test_pagination_bounds(client, doctor):
    for query in ("page=0", "page=-1", "page_size=0", "page_size=101"):
        assert client.get(f"{API}/doctor/appointments?{query}", headers=doctor).status_code == 422
        assert client.get(f"{API}/doctor/agent-runs?{query}", headers=doctor).status_code == 422
    assert client.get(f"{API}/doctor/appointments?page=1&page_size=100", headers=doctor).status_code == 200
