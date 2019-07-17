from locust import HttpLocust, TaskSet

def lookup(l):
    l.client.post("/authenticate", {"login[username_or_email]":"admin"})

    # with l.client.get("/", catch_response=True) as response:
    #     print(response.content)

# def logout(l):
#     l.client.post("/logout")
#
# def index(l):
#     with l.client.get("/", catch_response=True) as response:
#         print(response.content)
#
# def profile(l):
#     l.client.get("/profile")

class UserBehavior(TaskSet):
    #tasks = {index: 2, profile: 1}

    def on_start(self):
        lookup(self)

    # def on_stop(self):
    #     logout(self)

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000