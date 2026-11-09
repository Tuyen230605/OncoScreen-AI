"""scheduler.tick (nhắc lịch đến hạn) và metrics_service (dashboard quan sát AI)."""

from datetime import date, timedelta

from app.database import SessionLocal
from app.models import AgentRun
from app.services import metrics_service, scheduler
from tests.conftest import API
from tests.test_journey import _patient_with_booking


def _finalize_with_due(client, doctor, due: date, email: str = "lan@test.vn") -> dict:
    patient, appt = _patient_with_booking(client, email=email)
    enc = client.post(f"{API}/doctor/appointments/{appt['id']}/start", headers=doctor).json()
    plan = enc["draft_plan"]
    plan["items"] = plan["items"][:1]
    plan["items"][0]["next_due"] = due.isoformat()
    r = client.post(
        f"{API}/doctor/encounters/{enc['id']}/finalize",
        json={"conclusion": "Khám vú chưa ghi nhận bất thường. Hẹn chụp nhũ ảnh.", "final_plan": plan},
        headers=doctor,
    )
    assert r.status_code == 200, r.text
    return patient


# --------------------------------------------------------------------------- scheduler.tick


def test_tick_marks_due_reminders_and_builds_message(client, doctor):
    patient = _finalize_with_due(client, doctor, date.today() - timedelta(days=1))
    assert client.get(f"{API}/reminders", headers=patient).json()[0]["status"] == "scheduled"

    assert scheduler.tick() == 1
    reminder = client.get(f"{API}/reminders?status=due", headers=patient).json()[0]
    assert reminder["status"] == "due"
    message = reminder["message"]
    assert message.startswith("lan@test.vn, ")  # tên bệnh nhân (helper đăng ký dùng email làm full_name)
    assert "không phải chẩn đoán" in message  # S1/S6: nhắc lịch không mang tính chẩn đoán

    assert scheduler.tick() == 0  # idempotent: không xử lý lại reminder đã due


def test_tick_includes_reminder_due_today(client, doctor):
    patient = _finalize_with_due(client, doctor, date.today())
    assert scheduler.tick() == 1
    assert client.get(f"{API}/reminders", headers=patient).json()[0]["status"] == "due"


def test_tick_ignores_future_and_completed_reminders(client, doctor):
    future = _finalize_with_due(client, doctor, date.today() + timedelta(days=30))
    done = _finalize_with_due(client, doctor, date.today() - timedelta(days=1), email="hoa@test.vn")
    reminder = client.get(f"{API}/reminders", headers=done).json()[0]
    assert client.post(f"{API}/reminders/{reminder['id']}/complete", json={}, headers=done).status_code == 200

    assert scheduler.tick() == 0
    assert client.get(f"{API}/reminders", headers=future).json()[0]["status"] == "scheduled"
    statuses = {r["status"] for r in client.get(f"{API}/reminders", headers=done).json()}
    assert "due" not in statuses  # reminder đã done không quay lại due; chu kỳ kế tiếp nằm ở tương lai


# --------------------------------------------------------------------------- metrics_service


def test_percentile_edge_cases():
    assert metrics_service._percentile([], 0.5) == 0.0
    assert metrics_service._percentile([7.0], 0.95) == 7.0
    values = [float(v) for v in range(1, 101)]
    assert metrics_service._percentile(values, 0.5) in {50.0, 51.0}
    assert metrics_service._percentile(values, 0.95) in {95.0, 96.0}
    assert metrics_service._percentile(values, 1.0) == 100.0


def test_metrics_on_empty_database():
    with SessionLocal() as db:
        m = metrics_service.metrics(db)
    assert m.consultations == 0 and m.agent_runs == 0 and m.appointments_by_status == {}
    assert m.agent_fallback_rate == 0.0 and m.agent_insufficient_rate == 0.0
    assert m.agent_latency_ms_p50 == 0.0 and m.agent_latency_ms_p95 == 0.0


def _add_runs(rows: list[tuple[str, float, bool, bool]]) -> None:
    with SessionLocal() as db:
        for i, (agent, latency, guard_blocked, insufficient) in enumerate(rows):
            db.add(
                AgentRun(
                    agent=agent,
                    trace_id=f"t{i}",
                    latency_ms=latency,
                    guard_blocked=guard_blocked,
                    insufficient_evidence=insufficient,
                    events=[],
                )
            )
        db.commit()


def test_metrics_rates_and_latency():
    _add_runs(
        [
            ("navigator", 10.0, False, False),
            ("navigator", 20.0, True, False),
            ("copilot", 30.0, False, True),
            ("copilot_qa", 400.0, True, True),
        ]
    )
    with SessionLocal() as db:
        m = metrics_service.metrics(db)
    assert m.agent_runs == 4
    assert m.agent_fallback_rate == 0.5 and m.agent_insufficient_rate == 0.5
    assert m.agent_latency_ms_p50 in {20.0, 30.0} and m.agent_latency_ms_p95 == 400.0


def test_agent_runs_filter_and_pagination():
    _add_runs([("navigator", 1.0, False, False)] * 5 + [("copilot", 1.0, False, False)] * 2)
    with SessionLocal() as db:
        page1 = metrics_service.agent_runs(db, "navigator", page=1, page_size=2)
        page3 = metrics_service.agent_runs(db, "navigator", page=3, page_size=2)
        everything = metrics_service.agent_runs(db, None, page=1, page_size=50)
    assert page1.total == 5 and len(page1.items) == 2 and {r.agent for r in page1.items} == {"navigator"}
    assert len(page3.items) == 1
    assert everything.total == 7


def test_metrics_endpoint_counts_journey(client, doctor):
    _finalize_with_due(client, doctor, date.today() + timedelta(days=30))
    m = client.get(f"{API}/doctor/metrics", headers=doctor).json()
    assert m["consultations"] == 1 and m["linked_consultations"] == 1 and m["booking_suggested"] == 1
    assert m["encounters_finalized"] == 1 and m["appointments_by_status"] == {"completed": 1}
    assert m["agent_runs"] >= 2  # navigator + copilot brief
