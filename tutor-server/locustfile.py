# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from lxml import html
from locust import HttpLocust, TaskSet  # , task
from random import choice, random

from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor

jsparser = Parser()


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


def become_random_teacher(loc):
    if not (hasattr(loc, 'csrf_param')):
            init_security_tokens(loc)
    search_path = ('/accounts/dev/accounts/search?'
                   'utf8=%E2%9C%93&'
                   'search%5Bquery%5D=teacher&'
                   'search%5Btype%5D=Any&commit=Search')
    res = loc.client.get(search_path)
    search_res = res.text
    tree = jsparser.parse(search_res)
    for node in nodevisitor.visit(tree):
        if (isinstance(node, ast.ExprStatement)
            and isinstance(node.expr.identifier, ast.DotAccessor)
            and node.expr.identifier.node.args[0].value ==
                '"#search-results"'):
            result = node.expr.args[0].value
            student_rows = html.fromstring(eval(result)).xpath('//td/a')
            student_url = choice(student_rows).xpath('./@href')[0]
            loc.client.post(student_url, data={'_method': 'post',
                                               loc.csrf_param: loc.csrf_token})
            return


def become_random_student(loc):
    if not (hasattr(loc, 'csrf_param')):
            init_security_tokens(loc)
    search_path = ('/accounts/dev/accounts/search?'
                   'utf8=%E2%9C%93&'
                   'search%5Bquery%5D=student&'
                   'search%5Btype%5D=Any&commit=Search')
    res = loc.client.get(search_path)
    search_res = res.text
    tree = jsparser.parse(search_res)
    for node in nodevisitor.visit(tree):
        if (isinstance(node, ast.ExprStatement)
            and isinstance(node.expr.identifier, ast.DotAccessor)
            and node.expr.identifier.node.args[0].value ==
                '"#search-results"'):
            result = node.expr.args[0].value
            student_rows = html.fromstring(eval(result)).xpath('//td/a')
            student_url = choice(student_rows).xpath('./@href')[0]
            loc.client.post(student_url, data={'_method': 'post',
                                               loc.csrf_param: loc.csrf_token})
            return


def extract_courses(loc):
    res = loc.client.get('/dashboard')
    h = html.fromstring(res.text)
    data = json.loads(h.xpath('//script[@type="application/json"]/text()')[0])
    return [c['id'] for c in data['courses']]


def index(loc):
    loc.client.get('/')


def visit_course(loc):
    course_id = choice(extract_courses(loc))
    loc.client.get(f'/course/{course_id}')


class UserBehavior(TaskSet):
    tasks = {index: 1, visit_course: 4}

    def on_start(self):
        if random() < 0.1:
            become_random_teacher(self)
        else:
            become_random_student(self)

    def on_stop(self):
        self.client.get('/accounts/logout')


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 0
    max_wait = 0
