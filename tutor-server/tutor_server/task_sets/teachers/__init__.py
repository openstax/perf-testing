from .base import TeacherBaseTaskSet

class TeacherPreviewCourseTaskSet(TeacherBaseTaskSet):
    tasks = {
        course_calendar: 2,
        course_roster: 4,
        course_performance: 10,
        course_spreadsheet: 2,
        course_question_library: 2,
        claim_preview: 1,
    }

    def on_start(self):
        self.claim_preview()


class TeacherTaskSet(TeacherBaseTaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        course_calendar: 1,
        course_roster: 2,
        course_performance: 5,
        course_spreadsheet: 1,
        course_question_library: 1,
    }
