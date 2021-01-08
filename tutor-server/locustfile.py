# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import logging
import os
import json

# from gevent import GreenletExit
from locust import HttpUser, TaskSet, between  # , task
from locust.exception import StopUser
from random import choice, random
from time import sleep, time
from urllib.parse import urlencode

from requests_html import HTML

MAXTRIES = 10
logger = logging.getLogger(__name__)

here = os.path.dirname(os.path.abspath(__file__))

logger.info(here)

users = {}
with open(os.path.join(here, "..", "..", "users.csv")) as f:
    for user in csv.DictReader(f, dialect="unix"):
        users.setdefault(user["type"], []).append((user["username"], user["password"]))


def init_security_tokens(ts):
    res = ts.client.get("/")

    res_html = HTML(url=res.url, html=res.text)
    login_url = res_html.xpath('//a[contains(@href, "login")]/@href')
    if len(login_url) > 0:
        ts.user.login_url = login_url[0]

    update_security_tokens(ts, res)

    # Parts of Rails insist on this
    ts.client.headers["X-Requested-With"] = "XMLHttpRequest"
    ts.client.headers["Accept"] = (
        "text/html,application/xhtml+xml,application/xml,"
        "application/json,text/plain,*/*"
    )
    # Need Chrome to get past CSRF, and AppleWebKit to get past browser.modern
    ts.client.headers["User-Agent"] = "Chrome/999.999.99 AppleWebKit/999.99 locust/1.0"


def update_security_tokens(ts, res=None):
    if res is None:
        res = ts.client.get("/")
    res_html = HTML(url=res.url, html=res.text)
    csrf_token = res_html.xpath("//meta[@name='csrf-token']/@content")[0]
    csrf_param = res_html.xpath("//meta[@name='csrf-param']/@content")[0]
    ts.csrf_token = csrf_token
    ts.csrf_param = csrf_param
    ts.client.headers["X-CSRF-Token"] = csrf_token


def login(ts, username, password):
    if not (hasattr(ts, "csrf_param")):
        init_security_tokens(ts)
    res = ts.client.get(ts.user.login_url, name="login url")
    res = submit_form(ts, res, data={"login_form[email]": username})
    res = submit_form(ts, res, data={"login_form[password]": password})

    # If password has expired, will redirect here
    if res.url.endswith("/password/reset"):
        res = reset_password(ts, res, password)

    # If there are terms to sign, will cycle back here until all are signed
    while "terms" in res.url:
        res = submit_form(ts, res)

    update_security_tokens(ts, res)
    return res


def reset_password(ts, res, password):
    data = {
        "set_password[password]": password,
        "set_password[password_confirmation]": password,
    }
    res = submit_form(ts, res, data)
    # One more click-through
    if res.url.endswith("reset_success"):
        return submit_form(ts, res)
    else:
        return res


def logout(ts):
    data = {"_method": "delete", "authenticity_token": getattr(ts, "csrf_token", "")}
    ts.client.headers.pop("X-Requested-With", None)
    ts.client.headers.pop("X-CSRF-Token", None)
    ts.client.post("/accounts/logout", data=data)
    try:
        for item in ["bootstrap", "user_type", "course", "course_data"]:
            delattr(ts.user, item)
    except AttributeError:
        pass

    try:
        for item in ["csrf_token", "csrf_param"]:
            delattr(ts, item)
    except AttributeError:
        pass


def become_random_user(ts, usertype=None):
    if usertype is None:
        usertype, username, password = choice(
            [(utype,) + utup for utype, ulist in users.items() for utup in ulist]
        )
    else:
        username, password = choice(users[usertype])

    become_user(ts, username, password)
    ts.user.user_type = usertype


def become_user(ts, username, password):
    dash = login(ts, username, password)
    res_html = HTML(url=dash.url, html=dash.text)
    j = res_html.xpath(
        '//body/script[@type="application/json" and @id="tutor-boostrap-data"]/text()'
    )
    if len(j) > 0:
        bootstrap = json.loads(j[0])
        #if bootstrap["user"]["available_terms"]:
        #    agree_to_tutor_terms(ts)
        ts.user.bootstrap = bootstrap
        ts.user.username = username
    else:
        logger.warning(f"Failed to login as user {username}")
        raise StopUser()

    return


def agree_to_tutor_terms(ts):
    terms = ts.client.get("/api/terms")
    term_ids = [str(t["id"]) for t in terms.json()]
    ts.client.put("/api/terms/" + ",".join(term_ids))


def become_random_student(ts):
    return become_random_user(ts, "student")


def become_random_teacher(ts):
    return become_random_user(ts, "teacher")


def new_user(ts):
    if random() < 0.1:
        ts.on_stop()
        ts.on_start()


# Common routines


def submit_form(ts, res, data={}, form_index=1):
    update_security_tokens(ts, res)
    res_html = HTML(url=res.url, html=res.text)
    form_action = res_html.xpath(f"((//form)[{form_index}])/@action")
    # _make_absolute strips last path component if action == ""
    if form_action and form_action != [""]:
        form_url = res_html._make_absolute(form_action[0])
    else:
        form_url = res.url

    form_method = res_html.xpath(f"((//form)[{form_index}])/@method")
    if form_method and form_method != [""]:
        form_method = form_method[0]
    else:
        form_method = "post"

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
    res = ts.client.request(form_method, form_url, data=form_data)
    return res


def index(ts):
    ts.client.get("/")


def updates(ts):
    ts.client.get("/api/updates")


def list_course_ids(ts):
    return [c["id"] for c in ts.user.bootstrap["courses"]]


# Student Routines


def visit_course(ts):
    course = choice(ts.user.bootstrap["courses"])
    ts.user.course = course
    course_id = course["id"]
    course_data = ts.client.get(
        f"/api/courses/{course_id}/dashboard", name="/api/courses/{course_id}/dashboard"
    ).json()
    ts.user.course_data = course_data
    if ts.user.user_type == "student":
        ts.client.get(
            f"/api/courses/{course_id}/guide", name="/api/courses/{course_id}/guide"
        )


def revise_course(ts, steptime=60):
    visit_course(ts)
    tasks = ts.user.course_data["tasks"]
    tasks_completed_steps = [
        t
        for t in tasks
        if t["type"] in ("homework", "reading") and t["completed_steps_count"] > 0
    ]
    for task in tasks_completed_steps:
        visit_completed_steps(ts, task["id"], steptime=steptime)


def visit_completed_steps(ts, taskid, steptime=60):
    ecosystem_id = ts.user.course["ecosystem_id"]
    book_uuid = ts.user.course["ecosystem_book_uuid"]
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

        sleep(random() * steptime)


def work_course_next_task(ts, steptime=300, number_steps=None):
    visit_course(ts)
    course_id = ts.user.course["id"]
    if not (hasattr(ts.user, "tasks_to_work")):
        tasks = ts.user.course_data["tasks"]
        tasks_not_completed = [
            t
            for t in tasks
            if t["type"] in ("homework", "reading")
            and t["completed_steps_count"] < t["steps_count"]
        ]
        tasks_not_completed.sort(key=lambda t: t["opens_at"])
        ts.user.tasks_to_work = tasks_not_completed

    tt = ts.user.tasks_to_work.pop()
    task = ts.client.get(
        f"/api/tasks/{tt['id']}", name="/api/tasks/{tt['id']}"
    ).json()
    logger.debug(f"Working task {task['title']}")
    work_task_steps(ts, task, steptime=steptime, number_steps=number_steps)
    # refresh course data local copy
    course_data = ts.client.get(
        f"/api/courses/{course_id}/dashboard", name="/api/courses/{course_id}/dashboard"
    ).json()
    ts.user.course_data = course_data


def work_course_practice_worst(ts, steptime=300):
    visit_course(ts)
    course_id = ts.user.course["id"]
    res = ts.client.post(
        f"/api/courses/{course_id}/practice/worst",
        name="/api/courses/{course_id}/practice/worst",
        json={},
    )
    logger.debug(res.text)
    # FIXME can the above fail?
    if res:
        task = res.json()
        logger.debug(f"Working task {task['title']} worst")
        work_task_steps(ts, task, steptime=steptime)


def work_course_practice_random_chapter(ts, steptime=10):
    visit_course(ts)
    course_id = ts.user.course["id"]
    guide = ts.client.get(
        f"/api/courses/{course_id}/guide", name="/api/courses/{course_id}/guide"
    ).json()
    chapter = choice(guide["children"])
    logger.info(f"Generating practice task for {chapter['title']}")
    task = generate_practice_task(ts, course_id, chapter["page_ids"])
    if task:
        logger.debug(f"Working task {task['title']} {chapter['title']}")
        work_task_steps(ts, task, steptime=steptime)


def work_course_practice_random_page(ts, steptime=10):
    visit_course(ts)
    course_id = ts.user.course["id"]
    guide = ts.client.get(
        f"/api/courses/{course_id}/guide", name="/api/courses/{course_id}/guide"
    ).json()
    pageid = choice(guide["page_ids"])
    logger.info(f"Generating practice task for page_id: {pageid}")
    task = generate_practice_task(ts, course_id, pageid)
    if task:
        logger.debug(f"Working task {task['title']} page_id: {pageid}")
        work_task_steps(ts, task, steptime=steptime)


def generate_practice_task(ts, course_id, page_ids=[]):
    start_time = time()
    task = ts.client.post(
        f"/api/courses/{course_id}/practice",
        name="/api/courses/{course_id}/practice",
        json={"page_ids": [page_ids]},
    ).json()

    placeholders = task["steps"][0]["type"] == "placeholder"
    if placeholders:
        tries = MAXTRIES
        while tries and placeholders:
            wait_time = 2 ** (MAXTRIES - tries) + 0.5 * random()
            tries -= 1
            sleep(wait_time)
            task = ts.client.get(
                f"/api/tasks/{task['id']}",
                name="/api/tasks/{task['id']} Practice retry",
            ).json()
            placeholders = task["steps"][0]["type"] == "placeholder"

        if placeholders:
            logger.info(
                f"Practice: failed after {MAXTRIES - tries} tries"
                f" {time() - start_time} sec task_id: {task['id']}"
            )
            task = None
        else:
            logger.info(
                f"Practice: succeeded after {MAXTRIES - tries} tries"
                f" {time() - start_time} sec to load task_id: {task['id']}"
            )

    else:
        logger.info(
            f"Practice: succeeded after 0 retries"
            f" {time() - start_time} sec to load task_id: {task['id']}"
        )

    return task


def work_task_steps(ts, task, steptime=300, number_steps=None):
    course = ts.user.course
    ts.client.get(
        f"/api/ecosystems/{course['ecosystem_id']}/readings",
        name="/api/ecosystems/{course['ecosystem_id']}/readings",
    ).json()
    ts.client.get(
        f"/api/books/{course['ecosystem_book_uuid']}/highlighted_sections",
        name="/api/books/{course['ecosystem_book_uuid']}/highlighted_sections",
    ).json()

    placeholders = False
    for step in task["steps"][:number_steps]:
        if step["is_completed"] is False:
            if step["type"] == "placeholder":
                placeholders = True
                continue
            logger.debug(f"Working {step['type']} step: {step['id']}")
            step_methods[step["type"]](ts, step["id"], steptime)

    # Update task steps - get personalized and spaced practice
    if placeholders and number_steps is None:
        tt = ts.client.get(
            f"/api/tasks/{task['id']}", name="/api/tasks/{task['id']}"
        ).json()
        for step in tt["steps"][:number_steps]:
            if step["is_completed"] is False:
                logger.debug(f"Working {step['type']} step: {step['id']}")
                step_methods[step["type"]](ts, step["id"], steptime)


def work_reading_step(ts, step_id, steptime=300):
    step = ts.client.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
    for page in step["related_content"]:
        ts.client.get(
            f"/api/pages/{page['uuid']}/notes", name="/api/pages/{page['uuid']}/notes"
        )
    # Consider variable sleeptime for differemt types/lengths of steps
    # FIXME do something about fetching videos, ans sleeping the length of them
    if "iframe" in step["html"]:
        html = HTML(html=step["html"])
        for frame in html.xpath("//iframe/@src"):
            ts.client.get(frame)
    sleep(random() * steptime)
    res = ts.client.patch(
        f"/api/steps/{step_id}",
        name="PATCH /api/steps/{step_id}",
        json={"is_completed": True, "response_validation": {}},
    )
    logger.debug(res)


def work_exercise_step(ts, step_id, steptime=300):
    step = ts.client.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
    # Consider variable sleeptime for different types/lengths of steps
    data = {"is_completed": True}
    for question in step["content"]["questions"]:
        if "free-response" in question["formats"]:
            # FIXME generate responses from … where?
            # FIXME a certain percentage should get invalid and retry
            free_response = "This is not a valid response"
            res = ts.client.get(
                f"{ts.user.bootstrap['response_validation']['url']}"
                f"?uid={question['id']}&response={free_response}",
                name="validation",
            )
            if res:
                response_validation = res.json()
                data["free_response"] = free_response
                data["response_validation"] = response_validation
            else:
                data["response_validation"] = {}
        else:
            data["response_validation"] = {}
        if "multiple-choice" in question["formats"]:
            answer_id = choice(question["answers"])["id"]
            data["answer_id"] = answer_id
    # FIXME what about multipart questions?
    sleep(random() * steptime)
    res = ts.client.patch(
        f"/api/steps/{step_id}", name="PATCH /api/steps/{step_id}", json=data
    )
    logger.debug(res)


def work_embedded_step(ts, step_id, steptime=300):
    step = ts.client.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
    if "iframe" in step["html"]:
        html = HTML(html=step["html"])
        for frame in html.xpath("//iframe/@src"):
            ts.client.get(frame)
    sleep(random() * steptime)
    res = ts.client.patch(
        f"/api/steps/{step_id}",
        name="PATCH /api/steps/{step_id}",
        json={"is_completed": True, "response_validation": {}},
    )
    logger.debug(res)


def work_placeholder_step(ts, step_id, steptime=300):
    pass


step_methods = {
    "reading": work_reading_step,
    "exercise": work_exercise_step,
    "interactive": work_embedded_step,
    "video": work_embedded_step,
    "placeholder": work_placeholder_step,
}

# Teacher routines


def course_offerings(ts):
    res = ts.client.get("/api/offerings")
    if res:
        return res.json()["items"]


def course_roster(ts):
    if not (hasattr(ts.user, "course")):
        visit_course(ts)
    ts.client.get(f"/api/courses/{ts.user.course['id']}/roster", name="roster")


def course_calendar(ts):
    if not (hasattr(ts.user, "course")):
        visit_course(ts)
    ts.client.get(f"/api/courses/{ts.user.course['id']}/dashboard", name="dashboard")


def course_performance(ts):
    if not (hasattr(ts.user, "course")):
        visit_course(ts)
    course_id = ts.user.course["id"]
    ts.client.get(
        f"/api/courses/{course_id}/teacher_guide",
        name="/api/courses/{course_id}/teacher_guide",
    )
    ts.client.get(f"/api/courses/{course_id}/performance", name="student scores")


def course_spreadsheet(ts):
    if not (hasattr(ts.user, "course")):
        visit_course(ts)
    job_url = ts.client.post(
        f"/api/courses/{ts.user.course['id']}/performance/export",
        name="student scores export",
    ).json()["job"]
    job = ts.client.get(job_url, name="student scores export job").json()
    while job["status"] in ("queued", "started"):
        sleep(1)
        job = ts.client.get(job_url, name="student scores export job").json()
    if job["status"] == "succeeded":
        ts.client.get(job["url"], name="student scores spreadsheet")
    else:
        logger.debug(job)


def course_question_library(ts):
    if not (hasattr(ts.user, "course")):
        visit_course(ts)
    ecosystem_id = ts.user.course["ecosystem_id"]
    course_id = ts.user.course["id"]
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


def claim_preview(ts):
    offerings = course_offerings(ts)
    if offerings:
        offering = choice(offerings)
        logger.debug(json.dumps(offering, indent=2))
        preview = ts.client.post(
            "/api/courses",
            json={
                "name": offering["title"],
                "offering_id": offering["id"],
                "num_sections": 1,
                "is_preview": True,
                "time_zone": "Central Time (US & Canada)",
                "copy_question_library": True,
                "term": offering["active_term_years"][0]["term"],
                "year": offering["active_term_years"][0]["year"],
            },
        )
        if preview:
            ts.user.course = preview.json()
            course_id = ts.user.course["id"]
            course_data = ts.client.get(
                f"/api/courses/{course_id}/dashboard",
                name="/api/courses/{course_id}/dashboard",
            ).json()
            ts.user.course_data = course_data
        else:
            logger.warning(
                "Failed to claim preview: {}".format(json.dumps(offering, indent=2))
            )


def flatten_to_pages(container):
    pages = []
    for child in container["children"]:
        if "children" in child:
            pages.extend(flatten_to_pages(child))
        else:
            pages.append(child["id"])
    return pages


class RevisingStudentBehavior(TaskSet):
    tasks = {index: 1, visit_course: 1, revise_course: 7, updates: 1}

    def on_start(self):
        become_random_student(self)


class PracticingStudentBehavior(TaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        work_course_practice_random_chapter: 5,
        work_course_practice_random_page: 8,
        updates: 1,
    }

    def on_start(self):
        become_random_student(self)


class PracticeWorstStudentBehavior(TaskSet):
    tasks = {work_course_practice_worst: 1}

    def on_start(self):
        become_random_student(self)


class TeacherPreviewCourseBehavior(TaskSet):
    tasks = {
        course_calendar: 2,
        course_roster: 4,
        course_performance: 10,
        course_spreadsheet: 2,
        course_question_library: 2,
        claim_preview: 1,
    }

    def on_start(self):
        become_random_teacher(self)
        claim_preview(self)


class TeacherBehavior(TaskSet):
    tasks = {
        index: 1,
        visit_course: 1,
        course_calendar: 1,
        course_roster: 2,
        course_performance: 5,
        course_spreadsheet: 1,
        course_question_library: 1,
    }

    def on_start(self):
        become_random_teacher(self)


class RevisingStudentUser(HttpUser):
    tasks = [RevisingStudentBehavior]
    weight = 9
    wait_time = between(1, 5)


class PracticingStudentUser(HttpUser):
    tasks = [PracticingStudentBehavior]
    weight = 9
    wait_time = between(1, 5)


class PracticeWorstStudentUser(HttpUser):
    tasks = [PracticeWorstStudentBehavior]
    weight = 9
    wait_time = between(1, 5)


class TeacherUser(HttpUser):
    tasks = [TeacherBehavior]
    weight = 1
    wait_time = between(1, 5)


class PreviewTeacherUser(HttpUser):
    tasks = [TeacherPreviewCourseBehavior]
    weight = 1
    wait_time = between(1, 5)
