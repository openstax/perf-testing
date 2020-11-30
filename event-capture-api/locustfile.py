from locust import HttpLocust, TaskSet, task, between
import uuid
import logging
import random
from random import choice
from string import ascii_uppercase

logger = logging.getLogger(__name__)

class ApiBehavior(TaskSet):
  def on_start(self):
    self.user_uuid = str(uuid.uuid4())
    self.client.verify = False
    logger.info("event capture load: on_start user {}".format(self.user_uuid ))

  def random_string(self):
    length = random.randrange(5, 15)
    return ''.join(choice(ascii_uppercase) for i in range(length))

  def post_event(self):
    post_params = {
      "events": [ {
          "data": {
            "app": self.random_string(),
            "target": "study_guides",
            "context": str(uuid.uuid4()),
            "flavor": "full-screen-v2",
            "medium": "red cow",
            "client_clock_occurred_at": '2020-10-06T18:14:22Z',
            "client_clock_sent_at": '2020-10-06T18:14:22Z',
            "type": 'org.openstax.ec.nudged_v1',
            "session_uuid": str(uuid.uuid4()),
            "session_order": 1
          }
        } ]
    }

    logger.info("Post to /api/v0/events {}".format(post_params))
    res = self.client.post("/api/v0/events", json=post_params, name="create event", verify=False)

    if res.status_code != 201:
      logger.error("Post error {}".format(res.text) )

    return res.status_code == 201

  @task
  def add_event(self):
    self.client.headers['loadtest_client_uuid'] = self.user_uuid
    success = self.post_event()

#     if success:
#       logger.info("Post success!".format(res.text) )

class EventsApiTest(HttpLocust):
  task_set = ApiBehavior
  wait_time = between(1.0, 2.0)
  host = "http://localhost:4004"
  sock = None

  def __init__(self):
    super(EventsApiTest, self).__init__()
