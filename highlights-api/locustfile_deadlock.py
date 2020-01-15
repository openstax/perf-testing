from locust import HttpLocust, TaskSet, task, between
import uuid
import logging
import random
from random import choice
from string import ascii_uppercase

logger = logging.getLogger(__name__)

highlights = []
user_uuid = str(uuid.uuid4())
scope_id = str(uuid.uuid4())
source_id = str(uuid.uuid4())

def load_highlights(loc):
  if len(highlights) >= 1000:
    return
  prev_highlight_id = None
  next_highlight_id = None
  for i in range(1, 1000):
    new_hl_id = str(uuid.uuid4())
    post_params = {
      "highlight": {
        "id": id,
        "source_type": "openstax_page",
        "source_id": source_id,
        "anchor": "id301",
        "highlighted_content": "red cow",
        "color": 'green',
        "scope_id": scope_id,
        "location_strategies": [{"type":"TextPositionSelector","start":"12","end":"10"}]
      }
    }
    if prev_highlight_id != None:
      post_params['highlight']['prev_highlight_id'] = prev_highlight_id
    res = loc.client.post("/api/v0/highlights", json=post_params)
    if res.status_code == 201:
      prev_highlight_id = new_hl_id
      highlights.append(new_hl_id)
  logger.info("load_highlights: adding {} new highlights".format(len(highlights)))

class DeadlockBehavior(TaskSet):
  def on_start(self):
    load_highlights(self)
    logger.info("on_start user {}, scope {}, source {}".format(user_uuid, scope_id, source_id))

  @task(1)
  def delete(self):
    self.client.headers['loadtest_client_uuid'] = user_uuid

    hl_id = highlights.pop(1)
    res = self.client.delete("/api/v0/highlights/{}".format(hl_id), name="delete highlights")
    if res.status_code != 200:
      logger.error("delete {}".format(res.text))

class HighlightsApiTest(HttpLocust):
  task_set = DeadlockBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
