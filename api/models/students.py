from enum import StrEnum

from sqlalchemy import Column, Integer, String

from .base import Base


class Gender(StrEnum):
    """性别枚举"""

    male = "male"
    female = "female"


class Student(Base):
    """学生表模型（精简版）"""

    __tablename__ = "students"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="学生ID")

    # 基本信息
    name = Column(String(100), nullable=False, comment="学生姓名")
    gender = Column(String(10), nullable=False, comment="性别：male/female")
    age = Column(Integer, nullable=True, comment="年龄")

    # 学籍信息
    student_id = Column(String(50), unique=True, index=True, nullable=False, comment="学号")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}', student_id='{self.student_id}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "student_id": self.student_id,
        }
