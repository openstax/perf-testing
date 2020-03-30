#!python3
import requests
from time import sleep

host_url = "https://tutor-load-ae.openstax.org"
server_url = "http://localhost:8089"
swarm_url = f"{server_url}/swarm"
stop_url = f"{server_url}/stop"
requests_url = f"{server_url}/stats/requests"
reset_url = f"{server_url}/stats/reset"

steps = range(50, 950, 50)
step_inc = 1

num_practices = 30
target_answers_inc = num_practices * 5

old_step = 0
num_runners = 0
posted_answers = 0
old_posted_answers = 0
answer_rate = 0

requests.get(reset_url)
for step in steps:
    requests.post(
        swarm_url, data={"locust_count": step, "hatch_rate": step_inc, "host": host_url}
    )
    tries = 0
    while num_runners < step:
        tries += 1
        reqs = requests.get(requests_url).json()
        num_runners = reqs["user_count"]
        answers_record = [r for r in reqs["stats"] if r["name"].startswith("PATCH")]
        if answers_record != []:
            posted_answers = answers_record[0]["num_requests"]
            answer_rate = answers_record[0]["current_rps"]
        print(num_runners, posted_answers, answer_rate, flush=True)
        sleep(2)
    else:
        old_posted_answers = posted_answers

    while posted_answers < old_posted_answers + target_answers_inc:
        reqs = requests.get(requests_url).json()
        num_runners = reqs["user_count"]
        answers_record = [r for r in reqs["stats"] if r["name"].startswith("PATCH")][0]
        posted_answers = answers_record["num_requests"]
        answer_rate = answers_record["current_rps"]
        print(num_runners, posted_answers, answer_rate, flush=True)
        sleep(2)

    old_step = step
    old_posted_answers = posted_answers
