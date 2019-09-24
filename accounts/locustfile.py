# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import logging

from random import choice, random
from lxml import html
from locust import HttpLocust, TaskSet
from slimit.parser import Parser

jsparser = Parser()
logger = logging.getLogger(__name__)

with open("users.csv") as f:
    users = list(csv.reader(f, dialect="unix"))[1:] #skipping headers

def init_security_tokens(loc):
    res = loc.client.get('/')
    res_html = html.fromstring(res.text)
    csrf_token = res_html.xpath("//meta[@name='csrf-token']/@content")[0]
    csrf_param = res_html.xpath("//meta[@name='csrf-param']/@content")[0]
    loc.csrf_token = csrf_token
    loc.csrf_param = csrf_param
    loc.client.headers['X-CSRF-Token'] = csrf_token
    loc.client.headers['X-Requested-With'] = 'XMLHttpRequest'
    loc.client.headers['User-Agent'] = 'Chrome/999.999.99 locust/1.0'


def login(loc, username, password):
    res = loc.client.get('/')
    res_html = html.fromstring(res.text)
    login_url = res_html.xpath('//form')[0].action
    data = {i.name:i.value for i in res_html.xpath("//form//input")}

    data['login[username_or_email]'] = username

    res2 = loc.client.post(login_url, data=data)
    res2_html = html.fromstring(res2.text)
    login2_url = res2_html.xpath('//form')[0].action

    data2 = {i.name: i.value for i in res2_html.xpath("//form//input")}
    data2['login[password]'] = password
    res3 = loc.client.post(login2_url, data=data2)

    #res4 = loc.client.get('/api/user')


def become_random_user(loc):
    if not (hasattr(loc, "csrf_param")):
        init_security_tokens(loc)

    _, username, password = choice(users)

    login(loc, username, password)

    return


def user_api(loc):
    loc.client.get('/api/user')


def index(loc):
    loc.client.get('/')


class UserBehavior(TaskSet):
    tasks = {user_api: 1}

    def on_start(self):
        become_random_user(self)

    def on_stop(self):
        self.client.get('/accounts/logout')


class GeneralUser(HttpLocust):
    task_set = UserBehavior
