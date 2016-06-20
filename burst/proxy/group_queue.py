# -*- coding: utf-8 -*-

"""
封装通过group_id来访问数据的功能
"""

from collections import defaultdict
import Queue


class GroupQueue(object):
    """
    通过group来区分的queue
    """

    max_size = None
    queue_dict = None

    def __init__(self, max_size=-1):
        self.max_size = max_size
        self.queue_dict = defaultdict(self._queue_factory)

    def _queue_factory(self):
        """
        生成queue的工厂
        :return:
        """
        return Queue.Queue(self.max_size)

    def put(self, group_id, item):
        """
        加入item
        如果成功返回True，如果失败返回False
        :param group_id:
        :param item:
        :return:
        """
        try:
            self.queue_dict[group_id].put_nowait(item)
            return True
        except Queue.Full:
            return False
        except:
            return False

    def get(self, group_id):
        if self.empty(group_id):
            return None
        else:
            return self.queue_dict[group_id].get_nowait()

    def clear(self, group_id):
        """
        清空
        :param group_id:
        :return:
        """
        self.queue_dict.pop(group_id, None)

    def clear_all(self):
        """
        清空所有
        :return:
        """
        self.queue_dict.clear()

    def empty(self, group_id):
        """
        判断是否是空的
        :param group_id:
        :return:
        """
        return self.queue_dict[group_id].empty()

    def qsize(self, group_id):
        """
        某个队列的size
        :param group_id:
        :return:
        """
        return self.queue_dict[group_id].qsize()
