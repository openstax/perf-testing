from locust import HttpLocust, TaskSet

from bs4 import BeautifulSoup

def lookup(l):
    with l.client.post("/auth/identity/callback", {"login[username_or_email]":"admin",
                                              "authenticity_token": "cJ+lhaRuDnRCq+N4zbudQ5TGwRzkvIvA5wYvuQMUD3jFHoC9D5bQx44Ak4glSrjWmST4ioJNCxwq1gMNYPOfqg==",
                                              "utf8": "✓",
                                              "login[source]": "authenticate",
                                              "commit": "Log+in"}, catch_response=True) as response:
        print(response.content)

    # with l.client.get("/profile", catch_response=True) as response:
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

class AccountsTasks(TaskSet):

    # def on_start(self):
    #     """
    #     on_start is called when a Locust start before,
    #     any task is scheduled
    #     """
    #     self.login()
    #
    # def login(self):
    #     resp = self.client.get("/login")
    #     parsed_html = BeautifulSoup(resp.content)
    #     form_build_id = parsed_html.body.find('input', {'name': 'form_build_id'})['value']
    #
    #     self.client.post("/lookup_login", {
    #         "login[username_or_email]": "admin",
    #         "form_id": "user_login_form",
    #         "authenticity_token": "cJ+lhaRuDnRCq+N4zbudQ5TGwRzkvIvA5wYvuQMUD3jFHoC9D5bQx44Ak4glSrjWmST4ioJNCxwq1gMNYPOfqg==",
    #         "form_build_id": form_build_id,
    #         "op": "Log in"
    #     })

    def on_start(self):
        lookup(self)

    # def on_stop(self):
    #     logout(self)

class WebsiteUser(HttpLocust):
    task_set = AccountsTasks
    min_wait = 5000
    max_wait = 9000