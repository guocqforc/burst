# -*- coding: utf-8 -*-

from collections import defaultdict
import Queue


class GroupQueue(object):
    """
    通过group来区分的queue
    """

    queue_dict = None

    def __init__(self):
        self.queue_dict = defaultdict(Queue.Queue)

    def put(self, group_id, item):
        return self.queue_dict[group_id].put_nowait(item)

    def get(self, group_id):
        return self.queue_dict[group_id].get_nowait()

    def empty(self, group_id):
        """
        判断是否是空的
        :param group_id:
        :return:
        """
        return self.queue_dict[group_id].empty()
