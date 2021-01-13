from functools import cached_property
from logging import getLogger

from locust import TaskSet

class BaseTaskSet(TaskSet):

    @cached_property
    def logger(self):
        return getLogger(self.__class__.__name__)

    def index(self):
        res = self.get("/")
        self.user.update_csrf_token(res)

    def updates(self):
        self.get("/api/updates")

    def list_course_ids(ts):
        return [c["id"] for c in ts.user.bootstrap["courses"]]
