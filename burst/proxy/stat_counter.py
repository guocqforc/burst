# -*- coding: utf-8 -*-
from collections import Counter


class StatCounter(object):

    """
    统计计算类
    """

    # 客户端连接数
    clients = 0
    # 客户端请求数
    client_req = 0
    # 客户端回应数
    client_rsp = 0
    # worker请求数
    worker_req = 0
    # worker回应数
    worker_rsp = 0
    # 作业完成时间统计
    jobs_time_counter = Counter()

    def trans_to_counter_value(self, value):
        """
        把时间计算为一个可以统计分布的数值
        :return:
        """

        for dst_value in (10, 50, 100, 500, 1000, 5000):
            if value < dst_value:
                return dst_value
        else:
            return 'more'

    def add_job_time(self, job_time):
        """
        添加一个新的时间
        :param job_time:
        :return:
        """

        counter_value = self.trans_to_counter_value(job_time)
        self.jobs_time_counter[counter_value] += 1
