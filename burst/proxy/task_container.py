# -*- coding: utf-8 -*-

"""
主要为了支持到worker能知道要给返回数据的问题
"""

import weakref

from ..share.log import logger


class TaskContainer(object):

    # 封装好的task
    task = None

    # 客户端连接的弱引用
    _client_conn_ref = None

    def __init__(self, task, client_conn):
        self.task = task
        self.client_conn = client_conn

    @property
    def client_conn(self):
        # 如果已经释放, ()会返回None
        return self._client_conn_ref()

    @client_conn.setter
    def client_conn(self, value):
        def on_del(reference):
            # 已验证，会删除
            logger.error('reference: %s deleted', reference)

        self._client_conn_ref = weakref.ref(value)
