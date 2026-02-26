import random
from models_db import (
    YearDB,
    SectionDB,
    SubjectDB,
    TeacherDB,
    TeacherAvailabilityDB,
    AcademicSettingsDB
)

def generate_timetable(db):

    settings = db.query(AcademicSettingsDB).first()

    days = [d.strip() for d in settings.day_labels.split(",")]
    hours = [h.strip() for h in settings.hour_labels.split(",")]

    timetable = {}
    teacher_busy = {}
    teacher_hours = {}

    teachers = db.query(TeacherDB).all()

    # Initialize teacher workload
    for teacher in teachers:
        teacher_hours[teacher.id] = 0

    # Initialize teacher busy slots
    for day in days:
        for hour in hours:
            teacher_busy[(day, hour)] = []

    sections = db.query(SectionDB).all()

    for section in sections:

        timetable[section.name] = {}

        year = db.query(YearDB).get(section.year_id)
        subjects = db.query(SubjectDB).filter(
            SubjectDB.year_id == year.id
        ).all()

        subject_pool = []

        # Core subjects
        for subject in subjects:
            if not subject.is_elective:
                subject_pool.extend(
                    [(subject, None)] * subject.hours_per_week
                )

        # Elective grouping
        elective_groups = {}
        for subject in subjects:
            if subject.is_elective:
                elective_groups.setdefault(
                    subject.elective_group, []
                ).append(subject)

        for group_name, group_subjects in elective_groups.items():
            # All electives in same group share slot count
            hours_required = group_subjects[0].hours_per_week
            subject_pool.extend(
                [("ELECTIVE_GROUP", group_subjects)] * hours_required
            )

        random.shuffle(subject_pool)

        slot_index = 0

        for day in days:
            for hour in hours:

                if slot_index < len(subject_pool):
                    entry = subject_pool[slot_index]
                else:
                    entry = None

                slot_index += 1

                if entry is None:
                    timetable[section.name][(day, hour)] = {
                        "subject": "Free",
                        "teacher": ""
                    }
                    continue

                # Core subject
                if entry[0] != "ELECTIVE_GROUP":

                    subject = entry[0]

                    eligible_teachers = [
                        t for t in subject.teachers
                        if teacher_hours[t.id] < t.max_hours
                        and t.id not in teacher_busy[(day, hour)]
                        and db.query(TeacherAvailabilityDB).filter(
                            TeacherAvailabilityDB.teacher_id == t.id,
                            TeacherAvailabilityDB.day == day,
                            TeacherAvailabilityDB.hour == hour,
                            TeacherAvailabilityDB.available == True
                        ).first()
                    ]

                    if eligible_teachers:
                        teacher = random.choice(eligible_teachers)
                        teacher_hours[teacher.id] += 1
                        teacher_busy[(day, hour)].append(teacher.id)

                        timetable[section.name][(day, hour)] = {
                            "subject": subject.name,
                            "teacher": teacher.name
                        }
                    else:
                        timetable[section.name][(day, hour)] = {
                            "subject": subject.name,
                            "teacher": "No Teacher"
                        }

                # Elective group
                else:

                    group_subjects = entry[1]
                    elective_output = []

                    for subject in group_subjects:

                        eligible_teachers = [
                            t for t in subject.teachers
                            if teacher_hours[t.id] < t.max_hours
                            and t.id not in teacher_busy[(day, hour)]
                            and db.query(TeacherAvailabilityDB).filter(
                                TeacherAvailabilityDB.teacher_id == t.id,
                                TeacherAvailabilityDB.day == day,
                                TeacherAvailabilityDB.hour == hour,
                                TeacherAvailabilityDB.available == True
                            ).first()
                        ]

                        if eligible_teachers:
                            teacher = random.choice(eligible_teachers)
                            teacher_hours[teacher.id] += 1
                            teacher_busy[(day, hour)].append(teacher.id)

                            elective_output.append(
                                f"{subject.name} ({teacher.name})"
                            )
                        else:
                            elective_output.append(
                                f"{subject.name} (No Teacher)"
                            )

                    timetable[section.name][(day, hour)] = {
                        "subject": " | ".join(elective_output),
                        "teacher": ""
                    }

    return timetable