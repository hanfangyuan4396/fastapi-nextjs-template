from services.students_service import StudentsService


def test_list_students_empty(db_session):
    service = StudentsService()
    resp = service.list_students(db=db_session, page=1, page_size=10)
    assert resp["code"] == 0
    assert resp["message"] == "ok"
    assert resp["data"]["items"] == []
    assert resp["data"]["page"] == 1
    assert resp["data"]["page_size"] == 10
    assert resp["data"]["total"] == 0
