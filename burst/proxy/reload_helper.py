# -*- coding: utf-8 -*-

from collections import defaultdict
from ..share import constants


class ReloadHelper(object):

    proxy = None
    status = None

    # 预备役workers，使用dict，可以保证判断的时候更准确
    workers_dict = None

    def __init__(self, proxy):
        self.status = constants.RELOAD_STATUS_STOPPED
        self.proxy = proxy
        self.workers_dict = defaultdict(set)

    def start(self):
        """
        启动
        :return:
        """
        if self.status != constants.RELOAD_STATUS_STOPPED:
            return False

        self.status = constants.RELOAD_STATUS_PREPARING
        return True

    def stop(self):
        """
        停止
        :return:
        """
        self.status = constants.RELOAD_STATUS_STOPPED
        self.workers_dict.clear()

    def add_worker(self, worker):
        """
        添加worker
        :param worker:
        :return:
        """
        self.workers_dict[worker.group_id].add(worker)

        if self.status == constants.RELOAD_STATUS_PREPARING and self._match_expect_workers():
            self.status = constants.RELOAD_STATUS_WORKERS_DONE

    def remove_worker(self, worker):
        """
        添加worker
        :param worker:
        :return:
        """
        if worker in self.workers_dict[worker.group_id]:
            self.workers_dict[worker.group_id].remove(worker)

            if self.status == constants.RELOAD_STATUS_WORKERS_DONE and not self._match_expect_workers():
                self.status = constants.RELOAD_STATUS_PREPARING

            return True
        else:
            return False

    def _match_expect_workers(self):
        """
        是否满足预期的workers
        :return:
        """

        for group_id, group_info in self.proxy.app.config['GROUP_CONFIG'].items():
            expect_count = group_info['count']

            if len(self.workers_dict[group_id]) != expect_count:
                # 只要找到一个没有满足的，就可以扔掉了
                return False
        else:
            return True

    @property
    def running(self):
        return self.status in (constants.RELOAD_STATUS_PREPARING, constants.RELOAD_STATUS_WORKERS_DONE)

    @property
    def workers_done(self):
        """
        workers是否已经准备好了
        :return:
        """
        return self.status == constants.RELOAD_STATUS_WORKERS_DONE
