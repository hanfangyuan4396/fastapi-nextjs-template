from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.students import Student
from utils.logging import get_logger

logger = get_logger()


class StudentsService:
    def list_students(self, *, db: Session, page: int = 1, page_size: int = 100) -> dict[str, Any]:
        try:
            page = max(1, page)
            page_size = max(1, min(page_size, 100))

            base_query = db.query(Student)
            total: int = base_query.count()
            items = base_query.order_by(Student.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

            return {
                "code": 0,
                "message": "ok",
                "data": {
                    "items": [it.to_dict() for it in items],
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                },
            }
        except Exception:
            logger.exception("List students failed")
            return {"code": 50001, "message": "查询学生列表失败"}

    def create_student(
        self, *, db: Session, name: str, gender: str, student_id: str, age: int | None = None
    ) -> dict[str, Any]:
        try:
            # 唯一键 student_id 冲突交由数据库约束抛错
            student = Student(name=name, gender=gender, age=age, student_id=student_id)
            db.add(student)
            db.commit()
            db.refresh(student)
            return {"code": 0, "message": "ok", "data": student.to_dict()}
        except Exception:
            db.rollback()
            logger.exception("Create student failed")
            return {"code": 50002, "message": "新增学生失败"}
