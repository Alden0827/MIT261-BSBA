import streamlit as st

def get_students_for_teacher(db, teacher_name):
    """
    Gets the list of students assigned to a specific teacher.
    A teacher is assigned to a student if the teacher's name is in the 'Teachers' array of a student's grade document.
    """
    if not teacher_name:
        return []

    # Find all grade entries that include the teacher
    grades_cursor = db.grades.find({"Teachers": teacher_name})

    student_ids = set()
    for grade in grades_cursor:
        student_ids.add(grade['StudentID'])

    if not student_ids:
        return []

    # Fetch student details for the collected student IDs
    students_cursor = db.students.find({"_id": {"$in": list(student_ids)}})

    students = list(students_cursor)

    return students
