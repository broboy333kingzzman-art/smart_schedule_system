from scheduler_db import generate_timetable
import streamlit as st
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models_db import (
    Base,
    StreamDB,
    DepartmentDB,
    YearDB,
    SectionDB,
    SubjectDB,
    TeacherDB,
    AcademicSettingsDB,
    TeacherAvailabilityDB
)

# Create tables
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Smart Schedule Admin",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Smart Schedule Admin Panel")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Academic Settings",
        "Manage Streams",
        "Manage Departments",
        "Manage Years",
        "Manage Sections",
        "Manage Subjects",
        "Manage Teachers",
        "Manage Availability",
        "Generate Timetable"
    ]
)

db: Session = SessionLocal()

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Streams", db.query(StreamDB).count())
    col2.metric("Departments", db.query(DepartmentDB).count())
    col3.metric("Years", db.query(YearDB).count())
    col4.metric("Sections", db.query(SectionDB).count())

    col5, col6 = st.columns(2)
    col5.metric("Subjects", db.query(SubjectDB).count())
    col6.metric("Teachers", db.query(TeacherDB).count())

    st.markdown("---")
st.subheader("⚠️ System Reset")

if st.button("Reset Entire System"):

    from sqlalchemy import inspect

    # Drop all tables
    Base.metadata.drop_all(bind=engine)

    # Recreate tables
    Base.metadata.create_all(bind=engine)

    st.success("System reset successfully. All data cleared.")
    st.rerun()

# =========================================================
# ACADEMIC SETTINGS
# =========================================================

elif page == "Academic Settings":

    st.subheader("🛠 Configure Academic Time Structure")

    settings = db.query(AcademicSettingsDB).first()

    working_days = st.number_input(
        "Number of Working Days", 1, 7,
        value=settings.working_days if settings else 5
    )

    hours_per_day = st.number_input(
        "Hours Per Day", 1, 12,
        value=settings.hours_per_day if settings else 6
    )

    day_labels = st.text_input(
        "Day Labels (comma separated)",
        value=settings.day_labels if settings else "Monday,Tuesday,Wednesday,Thursday,Friday"
    )

    hour_labels = st.text_input(
        "Hour Labels (comma separated)",
        value=settings.hour_labels if settings else "H1,H2,H3,H4,H5,H6"
    )

    if st.button("Save Settings"):

        if settings:
            settings.working_days = working_days
            settings.hours_per_day = hours_per_day
            settings.day_labels = day_labels
            settings.hour_labels = hour_labels
        else:
            db.add(AcademicSettingsDB(
                working_days=working_days,
                hours_per_day=hours_per_day,
                day_labels=day_labels,
                hour_labels=hour_labels
            ))

        db.commit()
        st.success("Academic settings saved.")

# =========================================================
# STREAMS
# =========================================================

elif page == "Manage Streams":

    st.subheader("➕ Add Stream")
    name = st.text_input("Stream Name")

    if st.button("Add Stream"):
        if name.strip():
            db.add(StreamDB(name=name))
            db.commit()
            st.success("Stream added.")
        else:
            st.error("Stream name required.")

    st.markdown("---")
    for stream in db.query(StreamDB).all():
        st.write(f"• {stream.name}")

# =========================================================
# DEPARTMENTS
# =========================================================

elif page == "Manage Departments":

    streams = db.query(StreamDB).all()

    if not streams:
        st.warning("Add a Stream first.")
    else:
        stream_map = {s.name: s.id for s in streams}
        selected = st.selectbox("Select Stream", list(stream_map.keys()))
        dept_name = st.text_input("Department Name")

        if st.button("Add Department"):
            if dept_name.strip():
                db.add(DepartmentDB(
                    name=dept_name,
                    stream_id=stream_map[selected]
                ))
                db.commit()
                st.success("Department added.")
            else:
                st.error("Department name required.")

        st.markdown("---")
        for dept in db.query(DepartmentDB).all():
            stream = db.query(StreamDB).get(dept.stream_id)
            st.write(f"• {dept.name} ({stream.name})")

# =========================================================
# YEARS
# =========================================================

elif page == "Manage Years":

    departments = db.query(DepartmentDB).all()

    if not departments:
        st.warning("Add a Department first.")
    else:
        dept_map = {d.name: d.id for d in departments}
        selected = st.selectbox("Select Department", list(dept_map.keys()))
        year_name = st.text_input("Year Name")

        if st.button("Add Year"):
            if year_name.strip():
                db.add(YearDB(
                    name=year_name,
                    department_id=dept_map[selected]
                ))
                db.commit()
                st.success("Year added.")
            else:
                st.error("Year name required.")

        st.markdown("---")
        for year in db.query(YearDB).all():
            dept = db.query(DepartmentDB).get(year.department_id)
            st.write(f"• {year.name} ({dept.name})")

# =========================================================
# SECTIONS
# =========================================================

elif page == "Manage Sections":

    years = db.query(YearDB).all()

    if not years:
        st.warning("Add a Year first.")
    else:
        year_map = {y.name: y.id for y in years}
        selected = st.selectbox("Select Year", list(year_map.keys()))
        section_name = st.text_input("Section Name")

        if st.button("Add Section"):
            if section_name.strip():
                db.add(SectionDB(
                    name=section_name,
                    year_id=year_map[selected]
                ))
                db.commit()
                st.success("Section added.")
            else:
                st.error("Section name required.")

        st.markdown("---")
        for section in db.query(SectionDB).all():
            year = db.query(YearDB).get(section.year_id)
            st.write(f"• {section.name} ({year.name})")

# =========================================================
# SUBJECTS
# =========================================================

elif page == "Manage Subjects":

    years = db.query(YearDB).all()

    if not years:
        st.warning("Add a Year first.")
    else:
        year_map = {y.name: y.id for y in years}
        selected = st.selectbox("Select Year", list(year_map.keys()))
        subject_name = st.text_input("Subject Name")
        hours = st.number_input("Hours Per Week", 1, 10)
        is_elective = st.checkbox("Is Elective?")
        elective_group = None

        if is_elective:
            elective_group = st.text_input("Elective Group Name")

        if st.button("Add Subject"):
            if subject_name.strip():
                db.add(SubjectDB(
                    name=subject_name,
                    hours_per_week=hours,
                    is_elective=is_elective,
                    elective_group=elective_group,
                    year_id=year_map[selected]
                ))
                db.commit()
                st.success("Subject added.")
            else:
                st.error("Subject name required.")

        st.markdown("---")
        for subject in db.query(SubjectDB).all():
            year = db.query(YearDB).get(subject.year_id)
            tag = "Elective" if subject.is_elective else "Core"
            st.write(f"• {subject.name} ({tag}) - {year.name}")

# =========================================================
# TEACHERS
# =========================================================

elif page == "Manage Teachers":

    subjects = db.query(SubjectDB).all()

    teacher_name = st.text_input("Teacher Name")
    max_hours = st.number_input("Max Weekly Hours", 1, 40, 20)

    subject_map = {s.name: s for s in subjects}
    selected_subjects = st.multiselect("Select Subjects", list(subject_map.keys()))

    if st.button("Add Teacher"):
        if teacher_name.strip() and selected_subjects:
            new_teacher = TeacherDB(
                name=teacher_name,
                max_hours=max_hours
            )
            for sub in selected_subjects:
                new_teacher.subjects.append(subject_map[sub])
            db.add(new_teacher)
            db.commit()
            st.success("Teacher added.")
        else:
            st.error("Fill all fields.")

    st.markdown("---")
    for teacher in db.query(TeacherDB).all():
        subject_list = ", ".join([s.name for s in teacher.subjects])
        st.write(f"• {teacher.name} | Max: {teacher.max_hours} | Subjects: {subject_list}")

# =========================================================
# AVAILABILITY
# =========================================================

elif page == "Manage Availability":

    settings = db.query(AcademicSettingsDB).first()

    if not settings:
        st.warning("Configure Academic Settings first.")
    else:
        teachers = db.query(TeacherDB).all()

        if not teachers:
            st.warning("Add teachers first.")
        else:
            teacher_map = {t.name: t for t in teachers}
            selected_teacher = st.selectbox("Select Teacher", list(teacher_map.keys()))
            teacher_obj = teacher_map[selected_teacher]

            days = [d.strip() for d in settings.day_labels.split(",")]
            hours = [h.strip() for h in settings.hour_labels.split(",")]

            existing = db.query(TeacherAvailabilityDB).filter(
                TeacherAvailabilityDB.teacher_id == teacher_obj.id
            ).all()

            existing_slots = {(e.day, e.hour): e.available for e in existing}

            availability = {}

            for hour in hours:
                cols = st.columns(len(days) + 1)
                cols[0].markdown(f"**{hour}**")

                for i, day in enumerate(days):
                    default = existing_slots.get((day, hour), True)
                    availability[(day, hour)] = cols[i + 1].checkbox(
                        day,
                        value=default,
                        key=f"{teacher_obj.id}_{day}_{hour}"
                    )

            if st.button("Save Availability"):

                db.query(TeacherAvailabilityDB).filter(
                    TeacherAvailabilityDB.teacher_id == teacher_obj.id
                ).delete()

                for (day, hour), value in availability.items():
                    db.add(TeacherAvailabilityDB(
                        teacher_id=teacher_obj.id,
                        day=day,
                        hour=hour,
                        available=value
                    ))

                db.commit()
                st.success("Availability updated.")
# =========================================================
# GENERATE TIMETABLE
# =========================================================

elif page == "Generate Timetable":

    settings = db.query(AcademicSettingsDB).first()

    if not settings:
        st.warning("Configure Academic Settings first.")
    else:

        if st.button("Generate Timetable"):

            timetable = generate_timetable(db)

            days = [d.strip() for d in settings.day_labels.split(",")]
            hours = [h.strip() for h in settings.hour_labels.split(",")]

            st.success("Timetable generated successfully!")

            for section_name, slots in timetable.items():

                st.markdown(f"## 📘 {section_name}")

                # Table Header
                header_cols = st.columns(len(days) + 1)
                header_cols[0].markdown("")
                for i, day in enumerate(days):
                    header_cols[i + 1].markdown(f"**{day}**")

                # Rows = Hours
                for hour in hours:
                    cols = st.columns(len(days) + 1)
                    cols[0].markdown(f"**{hour}**")

                    for i, day in enumerate(days):
                        entry = slots.get((day, hour), {
                            "subject": "Free",
                            "teacher": ""
                        })

                        subject = entry["subject"]

                        cols[i + 1].markdown(subject)

                st.markdown("---")
db.close()