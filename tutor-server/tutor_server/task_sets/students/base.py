from random import choice, random
from time import sleep, time

from ..base import BaseTaskSet

class StudentBaseTaskSet(BaseTaskSet):

    MAX_PRACTICE_TRIES = 10

    def visit_course(ts):
        course = choice(ts.user.bootstrap["courses"])
        ts.user.course = course
        course_id = course["id"]
        course_data = ts.get(
            f"/api/courses/{course_id}/dashboard", name="/api/courses/{course_id}/dashboard"
        ).json()
        ts.user.course_data = course_data
        if ts.user.user_type == "student":
            ts.get(
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
        task = ts.get(f"/api/tasks/{taskid}", name="/api/tasks/{taskid}").json()
        if task["type"] == "reading":
            ts.get(
                f"/api/ecosystems/{ecosystem_id}/readings",
                name="/api/ecosystems/{ecosystem_id}/readings",
            )
            ts.get(
                f"/api/books/{book_uuid}/highlighted_sections",
                name="/api/books/{book_uuid}/highlighted_sections",
            )
        stepids = [s["id"] for s in task["steps"] if s["is_completed"]]
        for stepid in stepids:
            step = ts.get(f"/api/steps/{stepid}", name="/api/steps/{stepid}").json()
            if step["type"] == "reading":
                for page in task["related_content"]:
                    ts.get(
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
        task = ts.get(
            f"/api/tasks/{tt['id']}", name="/api/tasks/{tt['id']}"
        ).json()
        self.logger.debug(f"Working task {task['title']}")
        work_task_steps(ts, task, steptime=steptime, number_steps=number_steps)
        # refresh course data local copy
        course_data = ts.get(
            f"/api/courses/{course_id}/dashboard", name="/api/courses/{course_id}/dashboard"
        ).json()
        ts.user.course_data = course_data

    def work_course_practice_worst(ts, steptime=300):
        visit_course(ts)
        course_id = ts.user.course["id"]
        res = ts.post(
            f"/api/courses/{course_id}/practice/worst",
            name="/api/courses/{course_id}/practice/worst",
            json={},
        )
        self.logger.debug(res.text)
        # FIXME can the above fail?
        if res:
            task = res.json()
            self.logger.debug(f"Working task {task['title']} worst")
            work_task_steps(ts, task, steptime=steptime)

    def work_course_practice_random_chapter(ts, steptime=10):
        visit_course(ts)
        course_id = ts.user.course["id"]
        guide = ts.get(
            f"/api/courses/{course_id}/guide", name="/api/courses/{course_id}/guide"
        ).json()
        chapter = choice(guide["children"])
        self.logger.info(f"Generating practice task for {chapter['title']}")
        task = generate_practice_task(ts, course_id, chapter["page_ids"])
        if task:
            self.logger.debug(f"Working task {task['title']} {chapter['title']}")
            work_task_steps(ts, task, steptime=steptime)

    def work_course_practice_random_page(ts, steptime=10):
        visit_course(ts)
        course_id = ts.user.course["id"]
        guide = ts.get(
            f"/api/courses/{course_id}/guide", name="/api/courses/{course_id}/guide"
        ).json()
        pageid = choice(guide["page_ids"])
        self.logger.info(f"Generating practice task for page_id: {pageid}")
        task = generate_practice_task(ts, course_id, pageid)
        if task:
            self.logger.debug(f"Working task {task['title']} page_id: {pageid}")
            work_task_steps(ts, task, steptime=steptime)

    def generate_practice_task(ts, course_id, page_ids=[]):
        start_time = time()
        task = ts.post(
            f"/api/courses/{course_id}/practice",
            name="/api/courses/{course_id}/practice",
            json={"page_ids": [page_ids]},
        ).json()

        placeholders = task["steps"][0]["type"] == "placeholder"
        if placeholders:
            tries = MAX_PRACTICE_TRIES
            while tries and placeholders:
                wait_time = 2 ** (MAX_PRACTICE_TRIES - tries) + 0.5 * random()
                tries -= 1
                sleep(wait_time)
                task = ts.get(
                    f"/api/tasks/{task['id']}",
                    name="/api/tasks/{task['id']} Practice retry",
                ).json()
                placeholders = task["steps"][0]["type"] == "placeholder"

            if placeholders:
                self.logger.info(
                    f"Practice: failed after {MAX_PRACTICE_TRIES - tries} tries"
                    f" {time() - start_time} sec task_id: {task['id']}"
                )
                task = None
            else:
                self.logger.info(
                    f"Practice: succeeded after {MAX_PRACTICE_TRIES - tries} tries"
                    f" {time() - start_time} sec to load task_id: {task['id']}"
                )

        else:
            self.logger.info(
                f"Practice: succeeded after 0 retries"
                f" {time() - start_time} sec to load task_id: {task['id']}"
            )

        return task

    def work_task_steps(ts, task, steptime=300, number_steps=None):
        course = ts.user.course
        ts.get(
            f"/api/ecosystems/{course['ecosystem_id']}/readings",
            name="/api/ecosystems/{course['ecosystem_id']}/readings",
        ).json()
        ts.get(
            f"/api/books/{course['ecosystem_book_uuid']}/highlighted_sections",
            name="/api/books/{course['ecosystem_book_uuid']}/highlighted_sections",
        ).json()

        placeholders = False
        for step in task["steps"][:number_steps]:
            if step["is_completed"] is False:
                if step["type"] == "placeholder":
                    placeholders = True
                    continue
                self.logger.debug(f"Working {step['type']} step: {step['id']}")
                step_methods[step["type"]](ts, step["id"], steptime)

        # Update task steps - get personalized and spaced practice
        if placeholders and number_steps is None:
            tt = ts.get(
                f"/api/tasks/{task['id']}", name="/api/tasks/{task['id']}"
            ).json()
            for step in tt["steps"][:number_steps]:
                if step["is_completed"] is False:
                    self.logger.debug(f"Working {step['type']} step: {step['id']}")
                    step_methods[step["type"]](ts, step["id"], steptime)

    def work_reading_step(ts, step_id, steptime=300):
        step = ts.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
        for page in step["related_content"]:
            ts.get(
                f"/api/pages/{page['uuid']}/notes", name="/api/pages/{page['uuid']}/notes"
            )
        # Consider variable sleeptime for differemt types/lengths of steps
        # FIXME do something about fetching videos, ans sleeping the length of them
        if "iframe" in step["html"]:
            html = HTML(html=step["html"])
            for frame in html.xpath("//iframe/@src"):
                ts.get(frame)
        sleep(random() * steptime)
        res = ts.patch(
            f"/api/steps/{step_id}",
            name="PATCH /api/steps/{step_id}",
            json={"is_completed": True, "response_validation": {}},
        )
        self.logger.debug(res)

    def work_exercise_step(ts, step_id, steptime=300):
        step = ts.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
        # Consider variable sleeptime for different types/lengths of steps
        data = {"is_completed": True}
        for question in step["content"]["questions"]:
            if "free-response" in question["formats"]:
                # FIXME generate responses from … where?
                # FIXME a certain percentage should get invalid and retry
                free_response = "This is not a valid response"
                res = ts.get(
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
        res = ts.patch(
            f"/api/steps/{step_id}", name="PATCH /api/steps/{step_id}", json=data
        )
        self.logger.debug(res)

    def work_embedded_step(ts, step_id, steptime=300):
        step = ts.get(f"/api/steps/{step_id}", name="/api/steps/{step_id}").json()
        if "iframe" in step["html"]:
            html = HTML(html=step["html"])
            for frame in html.xpath("//iframe/@src"):
                ts.get(frame)
        sleep(random() * steptime)
        res = ts.patch(
            f"/api/steps/{step_id}",
            name="PATCH /api/steps/{step_id}",
            json={"is_completed": True, "response_validation": {}},
        )
        self.logger.debug(res)

    def work_placeholder_step(ts, step_id, steptime=300):
        pass

    step_methods = {
        "reading": work_reading_step,
        "exercise": work_exercise_step,
        "interactive": work_embedded_step,
        "video": work_embedded_step,
        "placeholder": work_placeholder_step,
    }
