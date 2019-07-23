from realbrowserlocusts import FirefoxLocust, ChromeLocust, PhantomJSLocust
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locust import TaskSet, task

platform_url = "https://accounts-dev.openstax.org/"
login_username = "admin"
login_password = ""

class LocustUserBehavior(TaskSet):

    # Functions to Run on Start and End
    def on_start(self):
        self.client.timed_event_for_locust("Load", "Login Page", self.load_login_page)
        self.client.timed_event_for_locust("Enter", "Username", self.enter_login_username)
        self.client.timed_event_for_locust("Enter", "Password", self.enter_login_password)

    # Helper Functions
    def load_login_page(self):
        self.client.get(platform_url+'login')
        self.client.wait.until(EC.visibility_of_element_located((By.ID, 'login_username_or_email')), "Login field is visible.")

    def enter_login_username(self):
        login_field = self.client.find_element_by_id('login_username_or_email')
        login_field.send_keys(login_username)

        self.client.find_element_by_name('commit').click()

        self.client.wait.until(EC.visibility_of_element_located((By.ID, 'login_password')), "Password field is visible.")

    def enter_login_password(self):
        login_field = self.client.find_element_by_id('login_password')
        login_field.send_keys(login_password)

        self.client.find_element_by_name('commit').click()

        self.client.wait.until(EC.visibility_of_element_located((By.ID, 'application-body')), "Application body is visible.")

    # Main Tasks        
    @task(2)
    def query_api(self):
        self.client.get(platform_url+'api/user')

class LocustUser(ChromeLocust):
    host = "not really used"
    timeout = 30 #in seconds in waitUntil thingies
    min_wait = 100
    max_wait = 1000
    screen_width = 1200
    screen_height = 600
    task_set = LocustUserBehavior