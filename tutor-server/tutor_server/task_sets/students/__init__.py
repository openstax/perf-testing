from .base import StudentBaseTaskSet

class RevisingStudentTaskSet(StudentBaseTaskSet):
    tasks = {index: 1, visit_course: 1, revise_course: 7, updates: 1}


class PracticingStudentTaskSet(StudentBaseTaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        work_course_practice_random_chapter: 5,
        work_course_practice_random_page: 8,
        updates: 1,
    }


class PracticeWorstStudentTaskSet(StudentBaseTaskSet):
    tasks = {work_course_practice_worst: 1}
