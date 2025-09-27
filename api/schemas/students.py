from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StudentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(male|female)$")
    age: int | None = Field(None, ge=0, le=200)
    student_id: str = Field(..., min_length=1, max_length=50)


class StudentItem(BaseModel):
    id: int
    name: str
    gender: str
    age: int | None
    student_id: str


class StudentsListResponse(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None
