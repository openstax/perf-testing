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

COLORS = ['yellow', 'green', 'blue', 'purple', 'pink']

logger = logging.getLogger(__name__)


class ApiBehavior(TaskSet):
  def on_start(self):
    self.user_uuid = random.choice(USERS)
    self.source_ids = {}
    self.source_ids[str(uuid.uuid4())] = []
    self.source_ids[str(uuid.uuid4())] = []
    self.source_ids[str(uuid.uuid4())] = []
    self.source_ids[str(uuid.uuid4())] = []

    self.scope_id = str(uuid.uuid4())
    logger.info("on_start user {}, book {}".format(self.user_uuid, self.scope_id))

  def random_string(self):
    length = random.randrange(10, 5000)
    return ''.join(choice(ascii_uppercase) for i in range(length))

  def post_highlight(self, id, source_id, prev_highlight_id, next_highlight_id, annotation):
    logger.info('post_highlight. User {}, id {}, source_id {}, prev_highlight_id {}, scope_id {}'.format(self.user_uuid, id, source_id, prev_highlight_id, self.scope_id))

    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "annotation": self.random_string() if annotation else null,
        "prev_highlight_id": prev_highlight_id,
        "next_highlight_id": next_highlight_id,
        "color": random.choice(COLORS),
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post_note {}".format(res))

  @task(10)
  def get(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    source_id = random.choice(self.source_ids.keys())
    colors = random.sample(COLORS, random.randint(1, len(COLORS)))
    res = self.client.get("/api/v0/highlights?source_ids={}&source_type=openstax_page&color={}".format(source_id, ','.join(colors)))
    logger.info("get {}".format(res))

  @task(4)
  def get_summary(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    colors = random.sample(COLORS, random.randint(1, len(COLORS)))
    res = self.client.get("/api/v0/highlights/summary?source_type=openstax_page&color={}".format(','.join(colors)))
    logger.info("get_summary {}".format(res))

  # 2 highlights within one page (source), one book (scope) per add task
  @task(2)
  def add_highlight(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    source_id = random.choice(self.source_ids.keys())
    highlights = self.source_ids[source_id];

    i = random.randint(0, len(highlights) - 1) if len(highlights) > 0 else 0 
   
    prev_highlight = highlights[i-1]
    next_highlight = highlights[i]
      
    self.post_first(id, source_id, prev_highlight, next_highlight, random.choice([1,2,3,4]) < 2)

class HighlightsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
