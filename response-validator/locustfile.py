from locust import HttpLocust, TaskSet, task
import os
import logging

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.abspath(__file__))

logger.info(here)

with open(os.path.join(here, 'urls.txt')) as f:
    urls = f.readlines()


class UserBehavior(TaskSet):

    @task(1)
    def do_them_all(self):
        for url in urls:
            self.client.get(url)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
