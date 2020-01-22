from locust import HttpLocust, TaskSet, task, between
import uuid
import logging
import random
from random import choice
from string import ascii_uppercase

logger = logging.getLogger(__name__)

highlights = []
loading = False
user_uuid = str(uuid.uuid4())
scope_id = str(uuid.uuid4())
source_id = str(uuid.uuid4())

def load_highlights(loc):
  global highlights, loading, user_uuid, scope_id, source_id

  prev_highlight_id = None
  next_highlight_id = None

  for i in range(1, 50):
    new_hl_id = str(uuid.uuid4())
    post_params = {
      "highlight": {
        "id": new_hl_id,
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
      logger.info("perft: for hl {}, setting prev {}".format(new_hl_id, prev_highlight_id))

    loc.client.headers['loadtest_client_uuid'] = user_uuid
    res = loc.client.post("/api/v0/highlights", json=post_params, name="create")
    if res.status_code == 201:
      logger.info("perft: created new highlight {}, prev_highlight_id {}".format(new_hl_id, prev_highlight_id))
      prev_highlight_id = new_hl_id
      highlights.append(new_hl_id)
    else:
      logger.info("perft: failed to created new highlight {}, prev_highlight_id {}".format(new_hl_id, prev_highlight_id))

  logger.info("perft: load_highlights: adding {} new highlights".format(len(highlights)))

class DeadlockBehavior(TaskSet):
  def on_start(self):
    global highlights, loading, user_uuid, scope_id, source_id

    logger.info("perft: on_start user {}, scope {}, source {} about to try load_highlights".format(user_uuid, scope_id, source_id))

    if not loading:
      loading = True
      load_highlights(self)

    logger.info("perft: on_start finished for user {}, scope {}, source {}".format(user_uuid, scope_id, source_id))

  @task(1)
  def delete(self):
    global highlights, loading, user_uuid, scope_id, source_id

    if len(highlights) == 0:
      logger.info("perft: delete found no highlights to delete")
      return

    self.client.headers['loadtest_client_uuid'] = user_uuid

    hl_id = highlights.pop()
    res = self.client.delete("/api/v0/highlights/{}".format(hl_id), name="delete highlights")
    if res.status_code != 200:
      logger.error("perft: delete {}".format(res.text))

class HighlightsApiTest(HttpLocust):
  task_set = DeadlockBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(HighlightsApiTest, self).__init__()
