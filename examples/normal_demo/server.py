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


# 配置得放到config.from_object前面
NAME = 'normal_demo'
# ADMIN_ADDRESS = ('127.0.0.1', 7778)
GROUP_CONFIG = {
    1: {
        'count': 2,
    },
    10: {
        'count': 2,
    },
}
GROUP_ROUTER = lambda box: 1 if box.cmd == 1 else 10

STOP_TIMEOUT = 10

app = Burst()
app.config.from_object(__name__)


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
    logger.error('request: %s, client_ip: %s, worker: %s', request, request.client_ip, request.worker)
    return dict(
        ret=10
    )


app.register_blueprint(user.bp)
app.run()
