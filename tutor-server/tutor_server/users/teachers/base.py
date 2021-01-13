from ..base import BaseUser

class TeacherBaseUser(BaseUser):

    weight = 1

    def __init__(self):
        super().__init__('teacher')
