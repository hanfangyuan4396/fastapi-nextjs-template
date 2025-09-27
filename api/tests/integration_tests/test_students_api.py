API_PREFIX = "/api"


def test_create_and_list_students(client):
    payload = {"name": "Alice", "gender": "female", "student_id": "S1001", "age": 18}
    resp = client.post(f"{API_PREFIX}/students", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["id"] > 0
    assert data["student_id"] == payload["student_id"]

    list_resp = client.get(f"{API_PREFIX}/students?page=1&page_size=10")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert any(it["student_id"] == payload["student_id"] for it in items)
