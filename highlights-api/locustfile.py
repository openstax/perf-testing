from locust import HttpLocust, TaskSet, task, between
import uuid
import logging
import random
from random import choice
from string import ascii_uppercase

USERS = [
  ("a232450a-3685-44fc-9e1c-d025239aa540"),
  ("65ec45ac-8764-4815-914b-d7f05bebc57f"),
  ("5abb5c90-9745-474c-9915-065a6d287dd3"),
  ("0eb074c6-84cf-4a38-bd3f-8761fc4f0307"),
  ("172bf55a-58e1-4d81-8c8e-09f6d68d541f"),
  ("1af9d16f-91f1-455f-a2aa-d910a136ab38"),
  ("0eb074c6-84cf-4a38-bd3f-8761fc4f0307"),
  ("3ccc06f2-4192-443b-b1f1-87902f6e41cf"),
  ("66d6ae04-c48e-4e83-96fc-5c270b49c402"),
  ("bb9fa39f-0194-4b90-a06b-654661da2be7"),
  ("2f9525e9-4967-4f9a-9801-36926831d364")
]

logger = logging.getLogger(__name__)

class ApiBehavior(TaskSet):
  def on_start(self):
    self.user_uuid = random.choice(USERS)
    logger.info("on_start {}".format(self.user_uuid))

  def random_string(self):
    length = random.randrange(10, 5000)
    return ''.join(choice(ascii_uppercase) for i in range(length))

  def post_first_note(self, id, source_id, scope_id):
    logger.info('post_first (enter) {}, {}, {}'.format(id, source_id, scope_id))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "yellow cow",
        "color": "yellow",
        "annotation": self.random_string(),
        "scope_id": scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post {}".format(res))

  def post_note(self, id, source_id, prev_highlight_id, scope_id):
    logger.info('post (enter) {}, {}, {}, {}'.format(id, source_id, prev_highlight_id, scope_id ))

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
        "scope_id": scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post {}".format(res))

  def post_first(self, id, source_id, scope_id):
    logger.info('post_first (enter) {}, {}, {}'.format(id, source_id, scope_id))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "color": "pink",
        "scope_id": scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post {}".format(res))

  def post(self, id, source_id, prev_highlight_id, scope_id):
    logger.info('post (enter) {}, {}, {}, {}'.format(id, source_id, prev_highlight_id, scope_id ))
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "prev_highlight_id": prev_highlight_id,
        "color": "pink",
        "scope_id": scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post {}".format(res))

  @task(1)
  def get_info(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    res = self.client.get("/api/v0/info")
    logger.info("get_info {}".format(res))

  @task(2)
  def get(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    res = self.client.get("/api/v0/highlights?source_type=openstax_page&color=yellow")
    logger.info("get {}".format(res))

  # 2 highlights within one page (source), one book (scope) per add task
  @task(8)
  def add_highlight(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    scope_id = str(uuid.uuid4())

    source_ids = [
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4()))
    ]

    for source_id in source_ids:
      id = str(uuid.uuid4())
      self.post_first(id, source_id, scope_id)
      next_id = str(uuid.uuid4())
      self.post(next_id, source_id, id, scope_id)

  # 2 notes within one page (source), one book (scope) per add task
  @task(4)
  def add_note(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    scope_id = str(uuid.uuid4())

    source_ids = [
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4())),
      (str(uuid.uuid4()))
    ]

    for source_id in source_ids:
      id = str(uuid.uuid4())
      self.post_first_note(id, source_id, scope_id)
      next_id = str(uuid.uuid4())
      self.post_note(next_id, source_id, id, scope_id)


class HighlightsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
