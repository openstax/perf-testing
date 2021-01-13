from ...task_sets.students import (
    RevisingStudentTaskSet,
    PracticingStudentTaskSet,
    PracticeWorstStudentTaskSet
)

from .base import BaseStudentUser

class RevisingStudentUser(BaseStudentUser):
    tasks = [RevisingStudentTaskSet]


class PracticingStudentUser(BaseStudentUser):
    tasks = [PracticingStudentTaskSet]


class PracticeWorstStudentUser(BaseStudentUser):
    tasks = [PracticeWorstStudentTaskSet]
