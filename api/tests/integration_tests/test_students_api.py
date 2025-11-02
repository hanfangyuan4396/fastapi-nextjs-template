from sqlalchemy.orm import Session

from core.jwt_tokens import create_access_token
from tests.helpers import create_user

API_PREFIX = "/api"


def test_create_and_list_students(client, db_session: Session):
    # 创建管理员并生成访问令牌
    admin = create_user(db_session, "admin_students", "123456", role="admin")
    access = create_access_token(admin.id)
    headers = {"Authorization": f"Bearer {access}"}

    payload = {"name": "Alice", "gender": "female", "student_id": "S1001", "age": 18}
    resp = client.post(f"{API_PREFIX}/students", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["id"] > 0
    assert data["student_id"] == payload["student_id"]

    list_resp = client.get(f"{API_PREFIX}/students?page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert any(it["student_id"] == payload["student_id"] for it in items)


def test_user_cannot_create_students_forbidden(client, db_session: Session):
    # 普通用户
    user = create_user(db_session, "user_students", "123456", role="user")
    access = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {access}"}

    payload = {"name": "Bob", "gender": "male", "student_id": "S2001", "age": 19}
    resp = client.post(f"{API_PREFIX}/students", json=payload, headers=headers)
    assert resp.status_code == 403


def test_user_can_list_students(client, db_session: Session):
    # 先由管理员创建一条记录，确保列表非空
    admin = create_user(db_session, "admin_students_2", "123456", role="admin")
    admin_access = create_access_token(admin.id)
    admin_headers = {"Authorization": f"Bearer {admin_access}"}
    payload = {"name": "Cindy", "gender": "female", "student_id": "S3001", "age": 20}
    _ = client.post(f"{API_PREFIX}/students", json=payload, headers=admin_headers)

    # 普通用户访问列表应 200
    user = create_user(db_session, "user_students_2", "123456", role="user")
    user_access = create_access_token(user.id)
    user_headers = {"Authorization": f"Bearer {user_access}"}

    list_resp = client.get(f"{API_PREFIX}/students?page=1&page_size=10", headers=user_headers)
    assert list_resp.status_code == 200
