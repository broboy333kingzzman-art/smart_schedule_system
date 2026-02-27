import random
from models_db import (
    AcademicSettingsDB,
    StreamDB,
    DepartmentDB,
    YearDB,
    SectionDB,
    SubjectDB,
    TeacherDB,
    TeacherAvailabilityDB,
)


def generate_timetable(db):

    settings = db.query(AcademicSettingsDB).first()
    if not settings:
        return {}

    days = [d.strip() for d in settings.day_labels.split(",")]
    hours = [h.strip() for h in settings.hour_labels.split(",")]

    timetable = {}
    teacher_busy = {}
    teacher_load = {}

    # Initialize teacher busy tracker
    for day in days:
        for hour in hours:
            teacher_busy[(day, hour)] = []

    # Initialize teacher workload tracker
    teachers = db.query(TeacherDB).all()
    for teacher in teachers:
        teacher_load[teacher.id] = 0

    sections = db.query(SectionDB).all()

    for section in sections:

        # Get hierarchy
        year = db.query(YearDB).filter(
            YearDB.id == section.year_id
        ).first()
        if not year:
            continue

        department = db.query(DepartmentDB).filter(
            DepartmentDB.id == year.department_id
        ).first()
        if not department:
            continue

        stream = db.query(StreamDB).filter(
            StreamDB.id == department.stream_id
        ).first()
        if not stream:
            continue

        # Unique display key
        section_key = (
            f"{stream.name} | "
            f"{department.name} | "
            f"{year.name} | "
            f"{section.name}"
        )

        timetable[section_key] = {}

        subjects = db.query(SubjectDB).filter(
            SubjectDB.year_id == year.id
        ).all()

        subject_pool = []

        # Build subject pool
        for subject in subjects:
            hours_required = subject.hours_per_week or 0

            if not subject.is_elective:
                subject_pool.extend(
                    [(subject, None)] * hours_required
                )

        random.shuffle(subject_pool)

        for day in days:
            for hour in hours:

                assigned = False

                for entry in subject_pool:

                    subject, _ = entry

                    eligible_teachers = [
                        t for t in subject.teachers
                        if teacher_load[t.id] < t.max_hours_per_week
                    ]

                    for teacher in eligible_teachers:

                        # Check availability
                        availability = db.query(TeacherAvailabilityDB).filter(
                            TeacherAvailabilityDB.teacher_id == teacher.id,
                            TeacherAvailabilityDB.day == day,
                            TeacherAvailabilityDB.hour == hour
                        ).first()

                        if not availability:
                            continue

                        if not availability.is_available:
                            continue

                        if teacher.id in teacher_busy[(day, hour)]:
                            continue

                        # Assign
                        timetable[section_key][(day, hour)] = {
                            "subject": subject.name,
                            "teacher": teacher.name
                        }

                        teacher_busy[(day, hour)].append(teacher.id)
                        teacher_load[teacher.id] += 1

                        subject_pool.remove(entry)
                        assigned = True
                        break

                    if assigned:
                        break

                if not assigned:
                    timetable[section_key][(day, hour)] = {
                        "subject": "Free",
                        "teacher": ""
                    }

    return timetable