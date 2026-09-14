from tests.conftest import NORMAL_ANSWERS, register_and_login


def _pending_session(client, patient) -> str:
    s = client.post("/api/v1/sessions", headers=patient).json()
    client.post(f"/api/v1/sessions/{s['id']}/answers", json={"answers": NORMAL_ANSWERS}, headers=patient)
    return s["id"]


def test_doctor_sees_draft_patient_does_not(client, patient, doctor):
    sid = _pending_session(client, patient)
    as_doc = client.get(f"/api/v1/sessions/{sid}", headers=doctor).json()
    as_pat = client.get(f"/api/v1/sessions/{sid}", headers=patient).json()
    assert as_doc["draft_plan"] and as_doc["risk_assessment"]
    assert as_pat["draft_plan"] is None and as_pat["final_plan"] is None and as_pat["risk_assessment"] is None


def test_other_patient_cannot_read(client, patient):
    sid = _pending_session(client, patient)
    other = register_and_login(client, "other@test.vn", "patient")
    assert client.get(f"/api/v1/sessions/{sid}", headers=other).status_code == 404


def test_patient_cannot_review(client, patient):
    sid = _pending_session(client, patient)
    assert client.post(f"/api/v1/sessions/{sid}/review", json={"action": "approve"}, headers=patient).status_code == 403


def test_approve_creates_reminders_and_reveals_final_plan(client, patient, doctor):
    sid = _pending_session(client, patient)
    queue = client.get("/api/v1/doctor/sessions?status=pending_review", headers=doctor).json()
    assert queue["total"] == 1
    r = client.post(f"/api/v1/sessions/{sid}/review", json={"action": "approve"}, headers=doctor)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"
    as_pat = client.get(f"/api/v1/sessions/{sid}", headers=patient).json()
    assert as_pat["final_plan"]["items"] and as_pat["draft_plan"] is None
    assert len(as_pat["reminders"]) == len(as_pat["final_plan"]["items"])
    assert client.get("/api/v1/reminders", headers=patient).json()


def test_reject_requires_note_and_review_twice_is_409(client, patient, doctor):
    sid = _pending_session(client, patient)
    assert client.post(f"/api/v1/sessions/{sid}/review", json={"action": "reject"}, headers=doctor).status_code == 400
    ok = client.post(
        f"/api/v1/sessions/{sid}/review", json={"action": "reject", "note": "cần khám thêm"}, headers=doctor
    )
    assert ok.json()["status"] == "rejected"
    again = client.post(f"/api/v1/sessions/{sid}/review", json={"action": "approve"}, headers=doctor)
    assert again.status_code == 409
