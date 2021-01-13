from ...task_sets.teachers import TeacherTaskSet, TeacherPreviewCourseTaskSet

from .base import BaseTeacherUser

class TeacherUser(BaseTeacherUser):
    tasks = [TeacherTaskSet]


class PreviewTeacherUser(BaseTeacherUser):
    tasks = [TeacherPreviewCourseTaskSet]
