# -*- coding: utf-8 -*-

"""
主要为了支持到worker能知道要给返回数据的问题
"""

import weakref


class TaskContainer(object):

    # 封装好的task
    task = None

    # 客户端连接的弱引用
    _client_conn_ref = None

    # udp会使用到
    client_address = None

    def __init__(self, task, client_conn, client_address=None):
        self.task = task
        self.client_conn = client_conn
        self.client_address = client_address

    @property
    def client_conn(self):
        # 如果已经释放, ()会返回None
        return self._client_conn_ref()

    @client_conn.setter
    def client_conn(self, value):
        self._client_conn_ref = weakref.ref(value)

    def write_to_client(self, data):
        """
        响应
        :param data:
        :return:
        """
        if not self.client_conn:
            return False

        kwargs = dict()
        if self.client_address:
            # 是udp连接
            kwargs['address'] = self.client_address

        return self.client_conn.write(data, **kwargs)
