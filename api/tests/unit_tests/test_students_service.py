import pytest

from services.students_service import StudentsService


@pytest.mark.asyncio
async def test_list_students_empty(async_db_session):
    service = StudentsService()
    resp = await service.list_students(db=async_db_session, page=1, page_size=10)
    assert resp["code"] == 0
    assert resp["message"] == "ok"
    assert resp["data"]["items"] == []
    assert resp["data"]["page"] == 1
    assert resp["data"]["page_size"] == 10
    assert resp["data"]["total"] == 0
