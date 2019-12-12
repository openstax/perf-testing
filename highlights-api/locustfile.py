from locust import HttpLocust, TaskSet, task, between
import uuid
import logging
import random
from random import choice
from string import ascii_uppercase

USERS = [
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4())),
  (str(uuid.uuid4()))
]

logger = logging.getLogger(__name__)

class ApiBehavior(TaskSet):
  def on_start(self):
    self.user_uuid = random.choice(USERS)
    self.source_ids_highlights = [
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4()))
    ]
    self.source_ids_notes = [
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4()))
    ]
    self.scope_id = str(uuid.uuid4())
    logger.info("on_start user {}, book {}".format(self.user_uuid, self.scope_id))

  def random_string(self):
    length = random.randrange(10, 5000)
    return ''.join(choice(ascii_uppercase) for i in range(length))

  def post_first_note(self, id, source_id):
    logger.info('post_first_note.  User {}, id {}, source_id {}, scope_id {}'.format(self.user_uuid, id, source_id, self.scope_id))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "yellow cow",
        "color": "yellow",
        "annotation": self.random_string(),
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post_first_note {}".format(res))

  def post_note(self, id, source_id, prev_highlight_id):
    logger.info('post_note. User {}, id {}, source_id {}, prev_highlight_id {}, scope_id {}'.format(self.user_uuid, id, source_id, prev_highlight_id, self.scope_id))

    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "annotation": self.random_string(),
        "prev_highlight_id": prev_highlight_id,
        "color": "pink",
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post_note {}".format(res))

  def post_first(self, id, source_id):
    logger.info('post_first. User {}, id {}, source_id {}, scope_id {}'.format(self.user_uuid, id, source_id, self.scope_id))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "color": "pink",
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post_first {}".format(res))

  def post(self, id, source_id, prev_highlight_id):
    logger.info('post. User {}, id {}, source_id {}, prev_highlight_id {}, scope_id {}'.format(self.user_uuid, id, source_id, prev_highlight_id, self.scope_id ))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "prev_highlight_id": prev_highlight_id,
        "color": "pink",
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post {}".format(res))

  @task(10)
  def get(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    source_id = random.choice(self.source_ids_highlights + self.source_ids_notes)
    res = self.client.get("/api/v0/highlights?source_ids={}&source_type=openstax_page&color=yellow".format(source_id))
    logger.info("get {}".format(res))

  @task(4)
  def get_summary(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    res = self.client.get("/api/v0/highlights/summary?source_type=openstax_page&color=yellow")
    logger.info("get_summary {}".format(res))

  # 2 highlights within one page (source), one book (scope) per add task
  @task(2)
  def add_highlight(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    for source_id in self.source_ids_highlights:
      id = str(uuid.uuid4())
      self.post_first(id, source_id)
      next_id = str(uuid.uuid4())
      self.post(next_id, source_id, id)

  # 2 notes within one page (source), one book (scope) per add task
  @task(1)
  def add_note(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    for source_id in self.source_ids_notes:
      id = str(uuid.uuid4())
      self.post_first_note(id, source_id)
      next_id = str(uuid.uuid4())
      self.post_note(next_id, source_id, id)


class HighlightsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
