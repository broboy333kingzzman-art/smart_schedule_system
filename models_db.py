# models_db.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Table


class StreamDB(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    departments = relationship("DepartmentDB", back_populates="stream")


class DepartmentDB(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    stream_id = Column(Integer, ForeignKey("streams.id"))

    stream = relationship("StreamDB", back_populates="departments")
    years = relationship("YearDB", back_populates="department")


class YearDB(Base):
    __tablename__ = "years"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))

    department = relationship("DepartmentDB", back_populates="years")
    sections = relationship("SectionDB", back_populates="year")
    subjects = relationship("SubjectDB", back_populates="year")


class SectionDB(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    year_id = Column(Integer, ForeignKey("years.id"))

    year = relationship("YearDB", back_populates="sections")


class SubjectDB(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    hours_per_week = Column(Integer)
    is_elective = Column(Boolean, default=False)
    elective_group = Column(String, nullable=True)
    year_id = Column(Integer, ForeignKey("years.id"))

    year = relationship("YearDB", back_populates="subjects")

teacher_subject_association = Table(
    "teacher_subjects",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id")),
    Column("subject_id", Integer, ForeignKey("subjects.id"))
)
class TeacherDB(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    max_hours = Column(Integer)

    subjects = relationship(
        "SubjectDB",
        secondary=teacher_subject_association,
        backref="teachers"
    )
class TeacherAvailabilityDB(Base):
    __tablename__ = "teacher_availability"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    day = Column(String)
    hour = Column(String)
    available = Column(Boolean, default=True)

class AcademicSettingsDB(Base):
    __tablename__ = "academic_settings"

    id = Column(Integer, primary_key=True, index=True)
    working_days = Column(Integer)
    hours_per_day = Column(Integer)
    day_labels = Column(String)
    hour_labels = Column(String)