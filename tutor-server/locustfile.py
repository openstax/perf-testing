# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import logging
import os
import json

# from gevent import GreenletExit
from lxml import html
from locust import HttpLocust, TaskSet  # , task
from random import choice, random
from time import sleep

from requests_html import HTML

logger = logging.getLogger(__name__)

here = os.path.dirname(os.path.abspath(__file__))

logger.info(here)

users = {}
with open(os.path.join(here, "users.csv")) as f:
    for user in csv.DictReader(f, dialect="unix"):
        users.setdefault(user["type"], []).append((user["username"], user["password"]))


def init_security_tokens(ts):
    res = ts.client.get("/")
    res_html = html.fromstring(res.text)
    csrf_token = res_html.xpath("//meta[@name='csrf-token']/@content")[0]
    csrf_param = res_html.xpath("//meta[@name='csrf-param']/@content")[0]
    ts.csrf_token = csrf_token
    ts.csrf_param = csrf_param
    ts.client.headers["X-CSRF-Token"] = csrf_token
    ts.client.headers["X-Requested-With"] = "XMLHttpRequest"
    # Need Chrome to get past CSRF, and AppleWebKit to get past browser.modern
    ts.client.headers["User-Agent"] = "Chrome/999.999.99 AppleWebKit/999.99 locust/1.0"
    ts.locust.login_url = res_html.xpath('//a[contains(@href, "login")]/@href')[0]


def login(ts, username, password):
    res = ts.client.get(ts.locust.login_url, name="login url")
    res_html = HTML(url=res.url, html=res.text)
    login_url = res_html._make_absolute(res_html.xpath("((//form)[1])/@action")[0])
    data = {
        i.attrs.get("name"): i.attrs.get("value")
        for i in res_html.xpath("(//form)[1]//input")
    }
    data["login[username_or_email]"] = username
    res = ts.client.post(login_url, data=data)
    res_html = HTML(url=res.url, html=res.text)
    login_url = res_html._make_absolute(res_html.xpath("((//form)[1])/@action")[0])
    data = {
        i.attrs.get("name"): i.attrs.get("value")
        for i in res_html.xpath("(//form)[1]//input")
    }
    data["login[password]"] = password
    res = ts.client.post(login_url, data=data)


def logout(ts):
    data = {"_method": "delete", "authenticity_token": getattr(ts, "csrf_token", "")}
    ts.client.headers.pop("X-Requested-With", None)
    ts.client.post("/accounts/logout", data=data)


def become_random_user(ts, usertype=None):
    if not (hasattr(ts, "csrf_param")):
        init_security_tokens(ts)

    if usertype is None:
        usertype, username, password = choice(
            [(utype,) + u for utype, utup in users.items() for u in utup]
        )
    else:
        username, password = choice(users[usertype])

    login(ts, username, password)
    dash = ts.client.get("/")
    h = html.fromstring(dash.text)
    j = h.xpath(
        '//body/script[@type="application/json" and @id="tutor-boostrap-data"]/text()'
    )[0]
    ts.locust.bootstrap = json.loads(j)
    ts.locust.user_type = usertype
    return


def become_random_student(ts):
    return become_random_user(ts, "student")


def become_random_teacher(ts):
    return become_random_user(ts, "teacher")


def list_course_ids(ts):
    return [c["id"] for c in ts.locust.bootstrap["courses"]]


def index(ts):
    ts.client.get("/")


def new_user(ts):
    if random() < 0.1:
        ts.on_stop()
        ts.on_start()


def visit_course(ts):
    course_id = choice(list_course_ids(ts))
    course_data = ts.client.get(f"/api/courses/{course_id}/dashboard").json()
    ts.locust.course_data = course_data
    ts.locust.course_id = course_id
    if ts.locust.user_type == "teacher":
        guide_name = "teacher_guide"
    else:
        guide_name = "guide"
    ts.client.get(f"/api/courses/{course_id}/{guide_name}")


def revise_course(ts):
    visit_course(ts)
    tasks = ts.locust.course_data["tasks"]
    tasks_completed_steps = [t for t in tasks if t["completed_steps_count"] > 0]
    for task in tasks_completed_steps:
        visit_completed_steps(ts, task["id"])


def visit_completed_steps(ts, taskid):
    course_id = ts.locust.course_id
    task = ts.client.get(f"/api/tasks/{taskid}", name="/api/tasks/{taskid}").json()
    if task["type"] == "reading":
        ts.client.get(
            f"/api/courses/{course_id}/highlighted_sections",
            name="/api/courses/{course_id}/highlighted_sections",
        )
    stepids = [s["id"] for s in task["steps"] if s["is_completed"]]
    for stepid in stepids:
        step = ts.client.get(f"/api/steps/{stepid}", name="/api/steps/{stepid}").json()
        if step["type"] == "reading":
            chap, sect = step["chapter_section"]
            ts.client.get(
                f"/api/courses/{course_id}/notes/{chap}.{sect}",
                name="/api/courses/{course_id}/notes/{chap}.{sect}",
            )
        sleep(60)


def updates(ts):
    ts.client.get("/api/updates")


def ui_settings(ts):
    ts.client.get("/api/ui_settings")


def course_roster(ts):
    if not (hasattr(ts.locust, "course_id")):
        visit_course(ts)
    ts.client.get(f"/api/courses/{ts.locust.course_id}/roster", name="roster")


def course_performance(ts):
    if not (hasattr(ts.locust, "course_id")):
        visit_course(ts)
    ts.client.get(
        f"/api/courses/{ts.locust.course_id}/performance", name="student scores"
    )


def course_spreadsheet(ts):
    if not (hasattr(ts.locust, "course_id")):
        visit_course(ts)
    job_url = ts.client.post(
        f"/api/courses/{ts.locust.course_id}/performance/export",
        name="student scores export",
    ).json()["job"]
    job = ts.client.get(job_url, name="student scores export job").json()
    while job["status"] in ("queued", "started"):
        sleep(1)
        job = ts.client.get(job_url, name="student scores export job").json()
    ts.client.get(job["url"], name="student scores spreadsheet")


class StudentBehavior(TaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        revise_course: 7,
        new_user: 1,
        updates: 1,
        ui_settings: 1,
    }

    def on_start(self):
        become_random_student(self)

    def on_stop(self):
        sleep(random() * 5)
        logout(self)


class TeacherBehavior(TaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        course_roster: 2,
        course_performance: 5,
        course_spreadsheet: 1,
        ui_settings: 1,
    }

    def on_start(self):
        become_random_teacher(self)

    def on_stop(self):
        sleep(random() * 5)
        logout(self)


class StudentUser(HttpLocust):
    task_set = StudentBehavior
    weight = 9


class TeacherUser(HttpLocust):
    task_set = TeacherBehavior
    weight = 1
    min_wait = 1000
    max_wait = 5000
