import json
from random import choice
from time import sleep
from urllib.parse import urlencode

from ..base import BaseTaskSet

class TeacherBaseTaskSet(BaseTaskSet):

    def course_offerings(ts):
        res = ts.get("/api/offerings")
        if res:
            return res.json()["items"]

    def course_roster(ts):
        if not (hasattr(ts.user, "course")):
            visit_course(ts)
        ts.get(f"/api/courses/{ts.user.course['id']}/roster", name="roster")

    def course_calendar(ts):
        if not (hasattr(ts.user, "course")):
            visit_course(ts)
        ts.get(f"/api/courses/{ts.user.course['id']}/dashboard", name="dashboard")

    def course_performance(ts):
        if not (hasattr(ts.user, "course")):
            visit_course(ts)
        course_id = ts.user.course["id"]
        ts.get(
            f"/api/courses/{course_id}/teacher_guide",
            name="/api/courses/{course_id}/teacher_guide",
        )
        ts.get(f"/api/courses/{course_id}/performance", name="student scores")

    def course_spreadsheet(ts):
        if not (hasattr(ts.user, "course")):
            visit_course(ts)
        job_url = ts.post(
            f"/api/courses/{ts.user.course['id']}/performance/export",
            name="student scores export",
        ).json()["job"]
        job = ts.get(job_url, name="student scores export job").json()
        while job["status"] in ("queued", "started"):
            sleep(1)
            job = ts.get(job_url, name="student scores export job").json()
        if job["status"] == "succeeded":
            ts.get(job["url"], name="student scores spreadsheet")
        else:
            self.logger.debug(job)

    def course_question_library(ts):
        if not (hasattr(ts.user, "course")):
            visit_course(ts)
        ecosystem_id = ts.user.course["ecosystem_id"]
        course_id = ts.user.course["id"]
        readings = ts.get(
            f"/api/ecosystems/{ecosystem_id}/readings",
            name="/api/ecosystems/{ecosystem_id}/readings",
        ).json()
        book = readings[0]
        # Pick one chapter worth of pages at random
        query = {
            "course_id": course_id,
            "page_ids[]": flatten_to_pages(choice(book["children"])),
        }
        ts.get(
            f"/api/ecosystems/{ecosystem_id}/exercises?" + urlencode(query, doseq=True),
            name="/api/ecosystems/{ecosystem_id}/exercises",
        )

    def claim_preview(ts):
        offerings = course_offerings(ts)
        if offerings:
            offering = choice(offerings)
            self.logger.debug(json.dumps(offering, indent=2))
            preview = ts.post(
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
                course_data = ts.get(
                    f"/api/courses/{course_id}/dashboard",
                    name="/api/courses/{course_id}/dashboard",
                ).json()
                ts.user.course_data = course_data
            else:
                self.logger.warning(
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
