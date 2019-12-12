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

  def post_highlight(self, id, source_id, prev_highlight_id, next_highlight_id, randomly_add_note):
    logger.info('post_highlight. User {}, id {}, source_id {}, prev_highlight_id {}, scope_id {}'.format(self.user_uuid, id, source_id, prev_highlight_id, self.scope_id))

    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "color": random.choice(COLORS),
        "scope_id": self.scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }

    if randomly_add_note:
      post_params['highlight']['annotation'] = self.random_string()

    if prev_highlight_id != None:
      post_params['highlight']['prev_highlight_id'] = prev_highlight_id

    if next_highlight_id != None:
      post_params['highlight']['next_highlight_id'] = next_highlight_id

    res = self.client.post("/api/v0/highlights", json=post_params)
    logger.info("post_note {}".format(res))

  @task(10)
  def get(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    source_id = random.choice(self.source_ids.keys())
    color = random.choice(COLORS)
    res = self.client.get("/api/v0/highlights?source_ids={}&source_type=openstax_page&color={}".format(source_id, color))
    logger.info("get {}".format(res))

  @task(4)
  def get_summary(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    color = random.choice(COLORS)
    res = self.client.get("/api/v0/highlights/summary?source_type=openstax_page&color={}".format(color))
    logger.info("get_summary {}".format(res))

  # 2 highlights within one page (source), one book (scope) per add task
  @task(2)
  def add_highlight(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    source_id = random.choice(self.source_ids.keys())
    highlight_ids = self.source_ids[source_id]

    new_hl_id = str(uuid.uuid4())
    num_hls = len(highlight_ids)
    if num_hls == 0:
      self.post_highlight(new_hl_id, source_id, None, None, random.choice([1,2,3,4]) < 2)
      self.source_ids[source_id].append(new_hl_id)
    elif num_hls == 1:
      self.post_highlight(new_hl_id, source_id, highlight_ids[0], None, random.choice([1,2,3,4]) < 2)
      self.source_ids[source_id].append(new_hl_id)
    else:
      i = random.randint(1, len(highlight_ids)-1)
      prev_highlight_id = highlight_ids[i-1]
      next_highlight_id = highlight_ids[i]
      self.post_highlight(new_hl_id, source_id, prev_highlight_id, next_highlight_id, random.choice([1,2,3,4]) < 2)
      self.source_ids[source_id].insert(i, new_hl_id)

class HighlightsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
