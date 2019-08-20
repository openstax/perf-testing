from locust import HttpLocust


class MyLocust(HttpLocust):
    """
    Helper class to use when debugging locust tasks.

    Instantiate with host parameter, then use it as parent to instantiate
    a locust.TaskSet instance, then call task functions with that instance
    as first argument
    """

    def __init__(self, host="http://localhost"):
        self.host = host
        super().__init__()
