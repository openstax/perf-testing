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

    res = self.client.post("/api/v0/highlights", json=post_params, name="create with annotation" if randomly_add_note else "create")
    
    if res.status_code != 201:
      logger.error("post_note {}".format(res.text))

  @task(10)
  def get(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    source_id = random.choice(self.source_ids.keys())
    color = random.choice(COLORS)
    res = self.client.get("/api/v0/highlights?source_ids={}&source_type=openstax_page&color={}".format(source_id, color), name="get highlights")
    if res.status_code != 200:
      logger.error("get {}".format(res.text))

  @task(4)
  def get_summary(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    color = random.choice(COLORS)
    res = self.client.get("/api/v0/highlights/summary?source_type=openstax_page&color={}".format(color), name="get summary")
    if res.status_code != 200:
      logger.error("get_summary {}".format(res.text))

  @task(5)
  def get_multiple(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid

    all_source_ids = self.source_ids.keys()
    source_ids = ",".join(random.sample(all_source_ids, random.randint(2, min(5, len(all_source_ids)))))
    color = random.choice(COLORS)
    res = self.client.get("/api/v0/highlights?source_ids={}&source_type=openstax_page&color={}".format(source_ids, color), name="get highlights (multiple)")
    if res.status_code != 200:
      logger.error("get {}".format(res.text))

  # 2 highlights within one page (source), one book (scope) per add task
  @task(2)
  def add_highlight(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    source_id = random.choice(self.source_ids.keys())
    highlight_ids = self.source_ids[source_id]
    do_annotation = random.randint(0, 4) < 2
    num_existing = len(highlight_ids);
    i = random.randint(0, num_existing)

    new_hl_id = str(uuid.uuid4())
    prev_highlight_id = highlight_ids[i-1] if i > 0 else None
    next_highlight_id = highlight_ids[i] if num_existing > 0 and i < num_existing else None

    self.post_highlight(new_hl_id, source_id, prev_highlight_id, next_highlight_id, do_annotation)
    self.source_ids[source_id].insert(i, new_hl_id)

class HighlightsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
