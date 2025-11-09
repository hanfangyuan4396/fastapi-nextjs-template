import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.base import Base
from services.students_service import StudentsService


@pytest.mark.asyncio
async def test_list_students_empty():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_local() as session:
        service = StudentsService()
        resp = await service.list_students(db=session, page=1, page_size=10)
        assert resp["code"] == 0
        assert resp["message"] == "ok"
        assert resp["data"]["items"] == []
        assert resp["data"]["page"] == 1
        assert resp["data"]["page_size"] == 10
        assert resp["data"]["total"] == 0
    await engine.dispose()
