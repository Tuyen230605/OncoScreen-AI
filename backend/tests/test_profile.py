from tests.conftest import API, register_and_login


def test_patient_profile_lifecycle(client):
    auth = register_and_login(client, "new_patient@test.vn")
    assert client.get(f"{API}/patients/me/profile", headers=auth).status_code == 404
    profile_data = {
        "age": 40,
        "gender": "male",
        "genetics_history": ["lung_cancer_father"],
        "lifestyle": {"smoking": True, "pack_years": 15},
    }
    r = client.put(f"{API}/patients/me/profile", json=profile_data, headers=auth)
    assert r.status_code == 200 and r.json()["lifestyle"]["pack_years"] == 15
    assert client.get(f"{API}/patients/me/profile", headers=auth).json()["age"] == 40
    kinds = [e["kind"] for e in client.get(f"{API}/patients/me/record", headers=auth).json()["timeline"]]
    assert kinds.count("profile.updated") == 1


def test_lifestyle_is_typed_and_keeps_extra_fields(client):
    """pack_years âm từng làm hỏng mọi phiên tư vấn (500) và brief của bác sĩ (502) cho bệnh nhân này."""
    auth = register_and_login(client, "typed@test.vn")
    bad = {"age": 50, "gender": "male", "lifestyle": {"smoking": True, "pack_years": -5}}
    assert client.put(f"{API}/patients/me/profile", json=bad, headers=auth).status_code == 422
    assert client.get(f"{API}/patients/me/profile", headers=auth).status_code == 404
    good = {"age": 50, "gender": "male", "lifestyle": {"smoking": True, "pack_years": 20, "alcohol": "light", "x": 1}}
    r = client.put(f"{API}/patients/me/profile", json=good, headers=auth)
    assert r.status_code == 200
    assert r.json()["lifestyle"] == {"smoking": True, "pack_years": 20, "alcohol": "light", "x": 1}
    assert client.post(f"{API}/navigator/consultations", headers=auth).status_code == 201
