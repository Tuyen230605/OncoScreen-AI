from tests.conftest import register_and_login


def test_patient_profile_lifecycle(client):
    # 1. Đăng ký patient mới
    auth = register_and_login(client, "new_patient@test.vn", "patient")

    # 2. Chưa có profile -> GET trả về 404
    r = client.get("/api/v1/patients/me/profile", headers=auth)
    assert r.status_code == 404

    # 3. Chưa có profile mà tạo session -> 400
    r_session = client.post("/api/v1/sessions", headers=auth)
    assert r_session.status_code == 400

    # 4. Tạo profile -> 200
    profile_data = {
        "age": 40,
        "gender": "male",
        "genetics_history": ["lung_cancer_father"],
        "lifestyle": {"smoking": True, "pack_years": 15},
    }
    r_put = client.put("/api/v1/patients/me/profile", json=profile_data, headers=auth)
    assert r_put.status_code == 200
    res = r_put.json()
    assert res["age"] == 40
    assert res["gender"] == "male"
    assert res["genetics_history"] == ["lung_cancer_father"]
    assert res["lifestyle"]["pack_years"] == 15

    # 5. GET lại profile -> 200
    r_get = client.get("/api/v1/patients/me/profile", headers=auth)
    assert r_get.status_code == 200
    assert r_get.json()["age"] == 40


def test_merge_answers_by_question_id(client, patient):
    s = client.post("/api/v1/sessions", headers=patient).json()
    sid = s["id"]
    assert s["status"] == "collecting"

    # Lần 1: gửi smoking = True
    batch1 = [{"question_id": "smoking", "value": True}]
    r1 = client.post(f"/api/v1/sessions/{sid}/answers", json={"answers": batch1}, headers=patient)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["status"] == "collecting"
    assert len(body1["answers"]) == 1
    assert body1["answers"][0]["question_id"] == "smoking"
    assert body1["answers"][0]["value"] is True

    # Lần 2: gửi smoking = False (ghi đè) + alcohol = 'Không' (thêm mới)
    batch2 = [
        {"question_id": "smoking", "value": False},
        {"question_id": "alcohol", "value": "Không"},
    ]
    r2 = client.post(f"/api/v1/sessions/{sid}/answers", json={"answers": batch2}, headers=patient)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["status"] == "collecting"
    assert len(body2["answers"]) == 2

    ans_map = {a["question_id"]: a["value"] for a in body2["answers"]}
    assert ans_map["smoking"] is False  # Đã ghi đè từ True -> False
    assert ans_map["alcohol"] == "Không"
