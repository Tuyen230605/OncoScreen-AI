from tests.conftest import API, register_and_login, say, start_consultation


def test_anonymous_consultation_requires_token(client):
    cid, headers = start_consultation(client)
    assert client.get(f"{API}/navigator/consultations/{cid}").status_code == 401
    assert client.get(f"{API}/navigator/consultations/{cid}", headers={"X-Consult-Token": "wrong"}).status_code == 401
    assert client.get(f"{API}/navigator/consultations/{cid}", headers=headers).json()["linked"] is False


def test_navigator_suggests_booking_with_sources(client):
    cid, headers = start_consultation(client)
    body = say(client, cid, headers, "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú. Tôi nên tầm soát gì?")
    reply = body["last_reply"]
    assert reply["next_action"] == "suggest_booking"
    assert {s["cancer_type"] for s in reply["suggestions"]} == {"breast", "cervical", "colorectal"}
    assert all(s["sources"] for s in reply["suggestions"])
    assert reply["trace_events"] == []  # trace không lộ ra API công khai
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]


def test_red_flag_routes_to_urgent_care_and_persists(client):
    cid, headers = start_consultation(client)
    first = say(client, cid, headers, "Em sờ thấy một khối cứng ở vú")["last_reply"]
    assert first["red_flag"]["detected"] and first["next_action"] == "urgent_care"
    assert first["suggestions"] == [] and first["booking_hint"]["priority"] == "urgent"
    again = say(client, cid, headers, "Em 38 tuổi, nữ")["last_reply"]
    assert again["next_action"] == "urgent_care"


def test_quick_form_answers(client):
    cid, headers = start_consultation(client)
    questions = client.get(f"{API}/navigator/questionnaire").json()["questions"]
    assert questions[0]["id"] == "age"
    answers = [
        {"question_id": "age", "value": 55},
        {"question_id": "gender", "value": "Nam"},
        {"question_id": "smoking", "value": True},
        {"question_id": "pack_years", "value": 30},
    ]
    reply = say(client, cid, headers, answers=answers)["last_reply"]
    assert "lung" in {s["cancer_type"] for s in reply["suggestions"]}
    assert "lung_screening" in reply["booking_hint"]["service_codes"]


def test_empty_message_is_rejected(client):
    cid, headers = start_consultation(client)
    r = client.post(f"{API}/navigator/consultations/{cid}/messages", json={"message": "  "}, headers=headers)
    assert r.status_code == 422


def test_register_with_consultation_links_and_prefills_profile(client):
    cid, headers = start_consultation(client)
    say(client, cid, headers, "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú")
    token = headers["X-Consult-Token"]
    auth = register_and_login(client, "lan@test.vn", consultation_id=cid, consultation_token=token)
    profile = client.get(f"{API}/patients/me/profile", headers=auth).json()
    assert profile["age"] == 45 and profile["gender"] == "female"
    assert profile["genetics_history"] == ["breast_cancer_family"]
    record = client.get(f"{API}/patients/me/record", headers=auth).json()
    assert {"account.created", "consult.summary", "profile.updated"} <= {e["kind"] for e in record["timeline"]}
    assert record["consultations"][0]["linked"] is True
    # Phiên đã gắn: token cũ không còn đủ, chỉ chủ tài khoản đọc được
    assert client.get(f"{API}/navigator/consultations/{cid}", headers={"X-Consult-Token": token}).status_code == 404
    assert client.get(f"{API}/navigator/consultations/{cid}", headers=auth).status_code == 200
    # Không gắn được lần hai
    r = client.post(
        f"{API}/auth/register",
        json={
            "email": "x@test.vn",
            "password": "123456",
            "full_name": "X",
            "role": "patient",
            "consultation_id": cid,
            "consultation_token": token,
        },
    )
    assert r.status_code == 400


def test_existing_user_claims_consultation(client):
    auth = register_and_login(client, "hung@test.vn")
    cid, headers = start_consultation(client)
    say(client, cid, headers, "Đi ngoài ra máu mấy tuần nay")
    r = client.post(
        f"{API}/navigator/consultations/{cid}/claim", headers={**auth, "X-Consult-Token": headers["X-Consult-Token"]}
    )
    assert r.status_code == 200 and r.json()["linked"]
    kinds = {e["kind"] for e in client.get(f"{API}/patients/me/record", headers=auth).json()["timeline"]}
    assert "red_flag.detected" in kinds


def test_logged_in_patient_consultation_is_linked_immediately(client):
    auth = register_and_login(client, "minh@test.vn")
    cid, _ = start_consultation(client, auth)
    body = say(client, cid, auth, "Tầm soát ung thư là gì?")
    assert body["linked"] is True


def test_negative_or_non_finite_number_answers_are_rejected(client):
    cid, headers = start_consultation(client)
    url = f"{API}/navigator/consultations/{cid}/messages"
    for value in (-3, "-1,5", "nan", "inf"):
        r = client.post(url, json={"answers": [{"question_id": "pack_years", "value": value}]}, headers=headers)
        assert r.status_code == 422, value
    assert client.post(url, json={"answers": [{"question_id": "age", "value": -1}]}, headers=headers).status_code == 422
    ok = say(client, cid, headers, answers=[{"question_id": "pack_years", "value": "không rõ"}])
    assert ok["intake"]["pack_years"] is None


def test_agent_error_detail_is_not_leaked(client, monkeypatch):
    from ai_core.api import AgentError

    from app.services import agent_service

    class Broken:
        name = "mock"

        def navigate(self, **_):
            raise AgentError("validation error for IntakeProfile input_value=-3.0")

    monkeypatch.setattr(agent_service, "_agent", lambda: Broken())
    cid, headers = start_consultation(client)
    r = client.post(f"{API}/navigator/consultations/{cid}/messages", json={"message": "xin chào"}, headers=headers)
    assert r.status_code == 502
    assert "IntakeProfile" not in r.json()["detail"] and "input_value" not in r.json()["detail"]
