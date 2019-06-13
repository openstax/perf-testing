# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from locust import HttpLocust, TaskSet, task

with open('urls.txt') as f:
    urls = f.readlines()


class UserBehavior(TaskSet):

    @task(1)
    def do_them_all(self):
        for url in urls:
            self.client.get(url)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
