from tests.conftest import NORMAL_ANSWERS


def test_normal_flow_reaches_pending_review(client, patient):
    s = client.post("/api/v1/sessions", headers=patient).json()
    assert s["status"] == "collecting" and s["questionnaire"]["questions"]
    r = client.post(f"/api/v1/sessions/{s['id']}/answers", json={"answers": NORMAL_ANSWERS}, headers=patient)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending_review"
    assert body["draft_plan"] is None  # R1: patient không thấy draft
    assert body["disclaimer"]


def test_red_flag_stops_flow(client, patient):
    s = client.post("/api/v1/sessions", headers=patient).json()
    answers = [{"question_id": "symptom_lump", "value": True}]
    body = client.post(f"/api/v1/sessions/{s['id']}/answers", json={"answers": answers}, headers=patient).json()
    assert body["status"] == "red_flag"
    assert body["red_flag"]["detected"] is True
    assert body["draft_plan"] is None and body["final_plan"] is None


def test_partial_answers_keep_collecting(client, patient):
    s = client.post("/api/v1/sessions", headers=patient).json()
    body = client.post(
        f"/api/v1/sessions/{s['id']}/answers", json={"answers": NORMAL_ANSWERS[:2]}, headers=patient
    ).json()
    assert body["status"] == "collecting"


def test_answers_after_pending_is_409(client, patient):
    s = client.post("/api/v1/sessions", headers=patient).json()
    client.post(f"/api/v1/sessions/{s['id']}/answers", json={"answers": NORMAL_ANSWERS}, headers=patient)
    r = client.post(f"/api/v1/sessions/{s['id']}/answers", json={"answers": NORMAL_ANSWERS}, headers=patient)
    assert r.status_code == 409
