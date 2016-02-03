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
        首位 < 5，则变成5
        首位 > 5，则变成10
        即
        100，会变为500，即小于500
        600，会变成1000，即小于10000
        :return:
        """

        if value == 0:
            # 0 不用做处理
            return 0

        first_num = int(str(value)[0])
        replace_num = 5 if first_num < 5 else 10

        return value * replace_num / first_num

    def add_job_time(self, job_time):
        """
        添加一个新的时间
        :param job_time:
        :return:
        """

        counter_value = self.trans_to_counter_value(job_time)
        self.jobs_time_counter[counter_value] += 1
