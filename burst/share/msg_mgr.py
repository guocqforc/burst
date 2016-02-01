# -*- coding: utf-8 -*-

from collections import  defaultdict
from .. import constants
from ..log import logger
from group_queue import GroupQueue


class MsgDispatcher(object):
    """
    消息管理
    主要包括: 消息来了之后的分发
    """

    # 繁忙worker列表
    busy_workers_dict = None
    # 空闲
    idle_workers_dict = None
    # 消息队列
    group_queue = None

    def __init__(self):
        self.busy_workers_dict = defaultdict(set)
        self.idle_workers_dict = defaultdict(set)
        self.group_queue = GroupQueue()

    def sync_worker_status(self, worker):
        """
        同步worker的状态：空闲/繁忙
        此时worker的status，已经自己改过了
        :param worker:
        :return:
        """

        worker_id = id(worker)

        if worker.status == constants.WORKER_STATUS_BUSY:
            src_workers_dict = self.idle_workers_dict
            dst_workers_dict = self.busy_workers_dict
        else:
            src_workers_dict = self.busy_workers_dict
            dst_workers_dict = self.idle_workers_dict

        try:
            src_workers_dict[worker.group_id].remove(worker_id)
        except:
            logger.error('exc occur, worker: %s', worker, exc_info=True)
        finally:
            dst_workers_dict[worker.group_id].add(worker_id)

    def push_msg(self, group_id, item):
        """
        添加消息
        当新消息来得时候，应该先检查有没有空闲的worker，如果没有的话，才放入消息队列
        :return:
        """
        idle_workers = self.idle_workers_dict[group_id]
        if not idle_workers:
            self.group_queue.put(group_id, item)
            return

    def pop_msg(self, group_id):
        """
        弹出消息
        :return:
        """
        return self.group_queue.get(group_id)
