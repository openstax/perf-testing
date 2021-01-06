from mylocust import MyLocust
from locust import TaskSet
from locustfile import *
loc=MyLocust('https://tutor-load-ae.openstax.org')
ts=TaskSet(loc)
become_random_teacher(ts)
loc.username
