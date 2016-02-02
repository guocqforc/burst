# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from burst import Burst, Blueprint

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
        'count': 10,
    },
    10: {
        'count': 2,
    },
}, lambda box: 1 if box.cmd == 1 else 10)


@app.route(1)
def index(request):
    return dict(
        ret=10
    )


app.run('127.0.0.1', 7777)
