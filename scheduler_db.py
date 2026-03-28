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
        year = section.year
        if not year:
            continue

        department = year.department
        if not department:
            continue

        stream = department.stream
        if not stream:
            continue

        # Unique key
        section_key = (
            f"{stream.name} | "
            f"{department.name} | "
            f"{year.name} | "
            f"{section.name}"
        )

        timetable[section_key] = {}

        subjects = year.subjects

        # SAFETY: if no subjects → skip
        if not subjects:
            continue

        subject_pool = []

        # Build subject pool
        for subject in subjects:
            hours_required = int(subject.hours_per_week or 0)

            if hours_required <= 0:
                continue

            if not subject.is_elective:
                subject_pool.extend(
                    [(subject, None)] * hours_required
                )

        # SAFETY: if empty → skip
        if not subject_pool:
            continue

        random.shuffle(subject_pool)

        for day in days:
            for hour in hours:

                assigned = False

                for entry in list(subject_pool):

                    subject, _ = entry

                    # 🔥 FINAL SAFE TEACHER SELECTION
                    eligible_teachers = [
                        t for t in (subject.teachers or db.query(TeacherDB).all())
                        if (t.max_hours is None) or (teacher_load[t.id] < t.max_hours)
                    ]

                    for teacher in eligible_teachers:

                        availability = db.query(TeacherAvailabilityDB).filter(
                            TeacherAvailabilityDB.teacher_id == teacher.id,
                            TeacherAvailabilityDB.day == day,
                            TeacherAvailabilityDB.hour == hour
                        ).first()

                        # SAFETY: if availability not set → allow
                        if availability and not availability.available:
                            continue

                        if teacher.id in teacher_busy[(day, hour)]:
                            continue

                        # Assign subject
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