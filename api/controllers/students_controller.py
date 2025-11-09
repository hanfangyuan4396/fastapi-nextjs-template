from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from core.rbac import Admin, UserOrAdmin
from schemas.students import StudentCreateRequest, StudentsListResponse
from services.students_service import StudentsService
from utils.db import AsyncDbSession

router = APIRouter()


@router.get("/students", response_model=StudentsListResponse)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    _viewer: UserOrAdmin = None,
    db: AsyncDbSession = None,
) -> dict[str, Any]:
    service = StudentsService()
    return await service.list_students(db=db, page=page, page_size=page_size)


@router.post("/students")
async def create_student(
    payload: StudentCreateRequest,
    _admin: Admin = None,
    db: AsyncDbSession = None,
) -> dict[str, Any]:
    service = StudentsService()
    return await service.create_student(
        db=db,
        name=payload.name,
        gender=payload.gender,
        student_id=payload.student_id,
        age=payload.age,
    )
