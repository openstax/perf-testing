from functools import cached_property
from logging import getLogger
from os import getenv
from random import choice

from locust import between
from locust.contrib.fasthttp import FastHttpSession, FastHttpUser
from pyquery import PyQuery as pq

class BaseHttpSession(FastHttpSession):

    BASE_HEADERS = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml,"
            "application/json,text/plain,*/*"
        ),
        "User-Agent": "Chrome/999.999.99 AppleWebKit/999.99 locust/1.0"
    }

    csrf_token = None
    csrf_param = None

    def update_csrf_token(self, get_response=None):
        if get_response:
            pq_response = pq(get_response.text)
            self.csrf_token = pq_response.find('meta[name="csrf-token"]').attr("content")
            self.csrf_param = pq_response.find('meta[name="csrf-param"]').attr("content")
        else:
            self.csrf_token = None
            self.csrf_param = None

    @property
    def csrf_hash(self):
        if self.csrf_token and self.csrf_param:
            return {self.csrf_param: self.csrf_token}
        else:
            return {}

    def default_headers(self, ajax=True):
        extra_headers = {}
        if self.csrf_token:
            extra_headers.update({"X-CSRF-Token": self.csrf_token})
        if ajax:
            extra_headers.update({"X-Requested-With": "XMLHttpRequest"})

        return {**BASE_HEADERS, **extra_headers}

    def request(self, *args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = self.default_headers()

        return super().request(*args, **kwargs)

class BaseUser(FastHttpUser):

    abstract = True

    USERNAMES = {
      'student': [f"reviewstudent{i + 1}" for i in range(6)],
      'teacher': ["reviewteacher"]
    }

    PASSWORD = getenv("DEMO_USER_PASSWORD")

    wait_time = between(1, 5)

    def __init__(self, environment, user_type=None):
        super().super().__init__(environment)
        if self.host is None:
            raise LocustError(
                "You must specify the base host. Either in the host attribute in the User class, or on the command line using the --host option."
            )
        if not re.match(r"^https?://[^/]+", self.host, re.I):
            raise LocustError("Invalid host (`%s`), must be a valid base URL. E.g. http://example.com" % self.host)

        self.client = BaseHttpSession(
            self.environment,
            base_url=self.host,
            network_timeout=self.network_timeout,
            connection_timeout=self.connection_timeout,
            max_redirects=self.max_redirects,
            max_retries=self.max_retries,
            insecure=self.insecure,
        )

        self.user_type = user_type
        self.username = choice(self.USERNAMES[user_type])

    @cached_property
    def logger(self):
        return getLogger(self.__class__.__name__)

    def submit_form(self, form_get_response, data={}, form_index=1):
        self.update_csrf_token(form_get_response)

        form_get_query = pq(form_get_response.text)
        form_get_query.make_links_absolute(base_url=form_get_response.url)
        form = form_get_query.find("form").eq(form_index)

        form_action = form.attr("action")

        form_method = form.attr("method")
        if not form_method:
            form_method = "post"

        form_data = {}
        for input in form.find("input"):
            name = input.attr("name")
            value = input.attr("value")
            if name in form_data:
                if isinstance(form_data[name], list):
                    form_data[name].append(value)
                else:
                    form_data[name] = [form_data[name], value]
            else:
                form_data[name] = value
        form_data.update(data)

        return self.request(form_method, form_action, data=form_data)

    @cached_property
    def login_url(self):
        return pq(self.get("/").text).find("a.login").attr("href")

    def reset_password(self, reset_password_get_response):
        data = {
            "set_password[password]": self.PASSWORD,
            "set_password[password_confirmation]": self.PASSWORD,
        }
        reset_password_response = self.submit_form(reset_password_get_response, data)

        # One more click-through
        if reset_password_response.url.endswith("reset_success"):
            return self.submit_form(reset_password_response)
        else:
            return reset_password_response

    def sign_all_accounts_terms(self, terms_get_response):
        terms_response = terms_get_response

        # If there are terms to sign, will cycle back here until all are signed
        while "terms" in terms_response.url:
            terms_response = self.submit_form(terms_response)

        return terms_response

    def sign_all_tutor_terms(self):
        terms = self.get("/api/terms")
        term_ids = [str(term["id"]) for term in terms.json()]
        self.put("/api/terms/" + ",".join(term_ids))

    def login(self):
        login_response = self.get(self.login_url, name="login redirect")
        if login_response.url.endswith("/accounts/dev/accounts"):
            # Local dev login
            become_url = pq(login_response.text).find(f'a:Contains("{self.username}")').attr("href")

            # Dev login response is a JS redirect (turbolinks) so instead just reload the home page
            self.post(become_url)
            after_login_response = self.get("/")
        else:
            email_response = submit_form(
                    self, login_response, data={"login_form[email]": self.username})
            after_login_response = submit_form(
                    self, email_response, data={"login_form[password]": self.PASSWORD})

        # If password has expired, will redirect here
        if after_login_response.url.endswith("/password/reset"):
            after_login_response = self.reset_password(after_login_response)

        after_login_response = self.sign_all_accounts_terms(after_login_response)

        self.sign_all_tutor_terms()

        self.bootstrap_data = json.loads(pq(after_login_response.text).find(
                'body script#bootstrap-data[type="application/json"]').text())

        return after_login_response

    def logout(self, response):
        self.update_csrf_token(response)

        data = {"_method": "delete"}
        data.update(self.client.csrf_hash)
        self.client.update_csrf_token()

        self.client.headers.pop("X-Requested-With", None)
        self.client.post("/accounts/logout",
                data=data, headers=self.client.default_headers(ajax=False))
        self.client.headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            for item in [
                    "csrf_token", "csrf_param", "bootstrap_data"]:
                delattr(self, item)
        except AttributeError:
            pass

    def on_start(self):
        self.login()
