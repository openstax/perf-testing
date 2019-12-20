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
from urllib.parse import urlencode

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
    ts.client.headers["Accept"] = (
        "text/html,application/xhtml+xml,application/xml,"
        "application/json,text/plain,*/*"
    )
    # Need Chrome to get past CSRF, and AppleWebKit to get past browser.modern
    ts.client.headers["User-Agent"] = "Chrome/999.999.99 AppleWebKit/999.99 locust/1.0"
    ts.locust.login_url = res_html.xpath('//a[contains(@href, "login")]/@href')[0]


def login(ts, username, password):
    res = ts.client.get(ts.locust.login_url, name="login url")
    res = submit_form(ts, res, data={"login[username_or_email]": username})
    res = submit_form(ts, res, data={"login[password]": password})

    # If password has expired, will redirect here
    if res.url.endswith("/password/reset"):
        res = reset_password(ts, res, password)

    # If there are terms to sign, will cycle back here until all are signed
    while "terms" in res.url:
        res = submit_form(ts, res)


def reset_password(ts, res, password):
    data = {
        "set_password[password]": password,
        "set_password[password_confirmation]": password,
    }
    return submit_form(ts, res, data)


def submit_form(ts, res, data={}, form_index=1):
    res_html = HTML(url=res.url, html=res.text)
    form_action = res_html.xpath(f"((//form)[{form_index}])/@action")[0]
    if form_action:
        form_url = res_html._make_absolute(form_action)
    else:
        form_url = res.url

    form_data = {}
    for i in res_html.xpath(f"(//form)[{form_index}]//input"):
        name = i.attrs.get("name")
        val = i.attrs.get("value")
        if name in form_data:
            if isinstance(form_data[name], list):
                form_data[name].append(val)
            else:
                form_data[name] = [form_data[name], val]
        else:
            form_data[name] = val
    form_data.update(data)
    res = ts.client.post(form_url, data=form_data)
    return res


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
    bootstrap = json.loads(j)
    if bootstrap["user"]["terms_signatures_needed"]:
        agree_to_tutor_terms(ts)
    ts.locust.bootstrap = bootstrap
    ts.locust.user_type = usertype
    return


def agree_to_tutor_terms(ts):
    terms = ts.client.get("/api/terms")
    term_ids = [str(t["id"]) for t in terms.json()]
    ts.client.put("/api/terms/" + ",".join(term_ids))


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
    course = choice(ts.locust.bootstrap["courses"])
    ts.locust.course = course
    course_id = course["id"]
    course_data = ts.client.get(
        f"/api/courses/{course_id}/dashboard", name="/api/courses/{course_id}/dashboard"
    ).json()
    ts.locust.course_data = course_data
    if ts.locust.user_type == "teacher":
        guide_name = "teacher_guide"
    else:
        guide_name = "guide"
    ts.client.get(
        f"/api/courses/{course_id}/{guide_name}",
        name=f"/api/courses/{{course_id}}/{guide_name}",
    )


def revise_course(ts, steptime=60):
    visit_course(ts)
    tasks = ts.locust.course_data["tasks"]
    tasks_completed_steps = [
        t
        for t in tasks
        if t["type"] in ("homework", "reading") and t["completed_steps_count"] > 0
    ]
    for task in tasks_completed_steps:
        visit_completed_steps(ts, task["id"], steptime=steptime)


def visit_completed_steps(ts, taskid, steptime=60):
    ecosystem_id = ts.locust.couse["ecosystem_id"]
    book_uuid = ts.locust.course["ecosystem_book_uuid"]
    task = ts.client.get(f"/api/tasks/{taskid}", name="/api/tasks/{taskid}").json()
    if task["type"] == "reading":
        ts.client.get(
            f"/api/ecosystems/{ecosystem_id}/readings",
            name="/api/ecosystems/{ecosystem_id}/readings",
        )
        ts.client.get(
            f"/api/books/{book_uuid}/highlighted_sections",
            name="/api/books/{book_uuid}/highlighted_sections",
        )
    stepids = [s["id"] for s in task["steps"] if s["is_completed"]]
    for stepid in stepids:
        step = ts.client.get(f"/api/steps/{stepid}", name="/api/steps/{stepid}").json()
        if step["type"] == "reading":
            for page in task["related_content"]:
                ts.client.get(
                    f"/api/pages/{page['uuid']}/notes",
                    name="/api/pages/{page_uuid}/notes",
                )

        sleep(steptime)


def work_course_task(ts, taskid, steptime=300):
    course_id = ts.locust.course["id"]
    task = ts.client.get(f"/api/tasks/{taskid}", name="/api/tasks/{taskid}").json()
    tasks_noncompleted_steps = []


def work_reading_step(ts, step_id):
    pass


def work_exercise_step(ts, step_id):
    pass


def updates(ts):
    ts.client.get("/api/updates")


def course_roster(ts):
    if not (hasattr(ts.locust, "course")):
        visit_course(ts)
    ts.client.get(f"/api/courses/{ts.locust.course['id']}/roster", name="roster")


def course_performance(ts):
    if not (hasattr(ts.locust, "course")):
        visit_course(ts)
    ts.client.get(
        f"/api/courses/{ts.locust.course['id']}/performance", name="student scores"
    )


def course_offerings(ts):
    ts.client.get("/api/offerings")


def course_spreadsheet(ts):
    if not (hasattr(ts.locust, "course")):
        visit_course(ts)
    job_url = ts.client.post(
        f"/api/courses/{ts.locust.course['id']}/performance/export",
        name="student scores export",
    ).json()["job"]
    job = ts.client.get(job_url, name="student scores export job").json()
    while job["status"] in ("queued", "started"):
        sleep(1)
        job = ts.client.get(job_url, name="student scores export job").json()
    if job["status"] == "succeeded":
        ts.client.get(job["url"], name="student scores spreadsheet")
    else:
        logger.info(job)


def course_question_library(ts):
    if not (hasattr(ts.locust, "course")):
        visit_course(ts)
    ecosystem_id = ts.locust.course["ecosystem_id"]
    course_id = ts.locust.course["id"]
    readings = ts.client.get(
        f"/api/ecosystems/{ecosystem_id}/readings",
        name="/api/ecosystems/{ecosystem_id}/readings",
    ).json()
    book = readings[0]
    # Pick one chapter worth of pages at random
    query = {
        "course_id": course_id,
        "page_ids[]": flatten_to_pages(choice(book["children"])),
    }
    ts.client.get(
        f"/api/ecosystems/{ecosystem_id}/exercises?" + urlencode(query, doseq=True),
        name="/api/ecosystems/{ecosystem_id}/exercises",
    )


def flatten_to_pages(container):
    pages = []
    for child in container["children"]:
        if "children" in child:
            pages.extend(flatten_to_pages(child))
        else:
            pages.append(child["id"])
    return pages


class StudentBehavior(TaskSet):
    tasks = {index: 1, visit_course: 1, revise_course: 7, updates: 1}

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
        course_question_library: 1,
        course_offerings: 1,
    }

    def on_start(self):
        become_random_teacher(self)

    def on_stop(self):
        sleep(random() * 5)
        logout(self)


class StudentUser(HttpLocust):
    task_set = StudentBehavior
    weight = 9
    min_wait = 1000
    max_wait = 5000


class TeacherUser(HttpLocust):
    task_set = TeacherBehavior
    weight = 1
    min_wait = 1000
    max_wait = 5000
