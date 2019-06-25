from locust import HttpLocust


class mylocust(HttpLocust):
    """
    Helper class to use when debugging locust tasks.

    Instantiate with host paramers, and call task functions
    with instance as first argument
    """
    def __init__(self, host='http://localhost'):
        self.host = host
        super().__init__()
