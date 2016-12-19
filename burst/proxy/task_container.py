# -*- coding: utf-8 -*-

"""
主要为了支持到worker能知道要给返回数据的问题
"""


class TaskContainer(object):

    # 封装好的task
    task = None

    # 客户端连接(udp可能是虚拟的)
    # 无需使用弱引用，因为task总会被分配，导致conn的引用减少
    client_conn = None

    def __init__(self, task, client_conn):
        self.task = task
        self.client_conn = client_conn
