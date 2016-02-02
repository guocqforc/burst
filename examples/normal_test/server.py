# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from burst import Burst, Blueprint
import user

import logging

LOG_FORMAT = '\n'.join((
    '/' + '-' * 80,
    '[%(levelname)s][%(asctime)s][%(process)d:%(thread)d][%(filename)s:%(lineno)d %(funcName)s]:',
    '%(message)s',
    '-' * 80 + '/',
))

logger = logging.getLogger('burst')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

app = Burst(Box, {
    1: {
        'count': 2,
    },
    10: {
        'count': 2,
    },
}, lambda box: 1 if box.cmd == 1 else 10)


@app.create_worker
def create_worker(worker):
    logger.error('create_worker: %r', worker)


@app.before_first_request
def before_first_request(request):
    logger.error('before_first_request')


@app.before_request
def before_request(request):
    logger.error('before_request')


@app.after_request
def after_request(request, exc):
    logger.error('after_request: %s', exc)


@app.before_response
def before_response(worker, rsp):
    logger.error('before_response: %r', rsp)


@app.after_response
def after_response(worker, rsp, result):
    logger.error('after_response: %r, %s', rsp, result)


@app.route(1)
def index(request):
    logger.error('request: %s, worker: %s', request, request.worker)
    return dict(
        ret=10
    )


app.register_blueprint(user.bp)
app.run('127.0.0.1', 7777)
