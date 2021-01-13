from ..base import BaseUser

class StudentBaseUser(BaseUser):

    weight = 9

    def __init__(self):
        super().__init__('student')
