# -*- coding: utf-8 -*-

"""
主要为了支持到worker能知道要给返回数据的问题
"""

import weakref
from burst.log import logger


class Task(object):

    # 客户端传过来的原始数据
    raw_data = None

    # raw_data 解析后的数据
    box = None

    # 客户端连接的弱引用
    _client_conn_ref = None

    def __init__(self, raw_data, box, client_conn):
        self.raw_data = raw_data
        self.box = box
        self.client_conn = client_conn

    @property
    def client_conn(self):
        # 如果已经释放, ()会返回None
        return self._client_conn_ref()

    @client_conn.setter
    def client_conn(self, value):
        def on_del(reference):
            logger.error('reference: %s deleted', reference)

        self._client_conn_ref = weakref.ref(value, on_del)
