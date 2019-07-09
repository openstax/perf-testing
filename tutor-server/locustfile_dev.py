# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import logging
import json

# from gevent import GreenletExit
from lxml import html
from locust import HttpLocust, TaskSet  # , task
from random import choice, random

from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor

jsparser = Parser()
logger = logging.getLogger(__name__)


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


def become_random_user(loc, search=''):
    if not (hasattr(loc, 'csrf_param')):
            init_security_tokens(loc)
    search_path = ('/accounts/dev/accounts/search?'
                   'utf8=%E2%9C%93&'
                   f'search%5Bquery%5D={search}&'
                   'search%5Btype%5D=Any&commit=Search')
    res = loc.client.get(search_path, name=f'find {search}')
    search_res = res.text
    tree = jsparser.parse(search_res)
    for node in nodevisitor.visit(tree):
        if (isinstance(node, ast.ExprStatement)
            and isinstance(node.expr.identifier, ast.DotAccessor)
            and node.expr.identifier.node.args[0].value ==
                '"#search-results"'):
            result = node.expr.args[0].value
            user_row = choice(html.fromstring(eval(result)).xpath('//td/a'))
            user_url = user_row.xpath('./@href')[0]
            user_id = user_row.xpath('./text()')[0].strip()
            loc.client.post(user_url, name=f'Become {user_id}',
                            data={'_method': 'post',
                                  loc.csrf_param: loc.csrf_token})

            # Now go to frontpage, which should redirect to /dashboard,
            # and load bootstrap data onto the local session instance
            dash = loc.client.get('/')
            h = html.fromstring(dash.text)
            j = h.xpath('//script[@type="application/json"]/text()')[0]
            loc.locust.data = json.loads(j)
            return


def become_random_student(loc):
    return become_random_user(loc, 'student')


def become_random_teacher(loc):
    return become_random_user(loc, 'teacher')


def list_course_ids(loc):
    return [c['id'] for c in loc.locust.data['courses']]


def index(loc):
    loc.client.get('/')


def new_user(loc):
    if random() < 0.1:
        loc.on_stop()
        loc.on_start()


def visit_course(loc):
    course_id = choice(list_course_ids(loc))
    loc.client.get(f'/course/{course_id}')


class StudentBehavior(TaskSet):
    tasks = {index: 1, visit_course: 4, new_user: 1}

    def on_start(self):
        become_random_student(self)

    def on_stop(self):
        self.client.get('/accounts/logout')


class TeacherBehavior(TaskSet):
    tasks = {index: 1, visit_course: 4}

    def on_start(self):
        become_random_teacher(self)

    def on_stop(self):
        self.client.get('/accounts/logout')


class StudentUser(HttpLocust):
    task_set = StudentBehavior
    stop_timeout = 1200
    weight = 9


class TeacherUser(HttpLocust):
    task_set = TeacherBehavior
    stop_timeout = 1200
    weight = 1
