# -*- coding: utf-8 -*-

import time
from twisted.internet.protocol import Protocol, Factory, connectionDone

from ..utils import safe_call
from ..log import logger
from .. import constants
from .job_box import JobBox


class WorkerConnectionFactory(Factory):

    def __init__(self, proxy, group_id):
        self.proxy = proxy
        self.group_id = group_id

    def buildProtocol(self, addr):
        return WorkerConnection(self, addr, self.group_id)


class WorkerConnection(Protocol):

    # 状态
    _status = None
    # 任务开始时间
    _job_begin_time = None

    # 正在处理的任务
    _doing_job = None
    # 读取缓冲
    _read_buffer = None

    def __init__(self, factory, address, group_id):
        """
        :param factory: 工厂类
        :param address: 地址
        :param group_id: 所属的组
        :return:
        """
        self.factory = factory
        self.address = address
        self.group_id = group_id
        self._read_buffer = ''

    def connectionMade(self):
        # 建立连接就直接去申请job
        self._try_alloc_job()

    def connectionLost(self, reason=connectionDone):
        # 要删除掉对应的worker
        self.factory.proxy.job_dispatcher.remove_worker(self)

    def dataReceived(self, data):
        """
        当数据接受到时
        :param data:
        :return:
        """
        self._read_buffer += data

        while self._read_buffer:
            # 因为box后面还是要用的
            job_box = JobBox()
            ret = job_box.unpack(self._read_buffer)
            if ret == 0:
                # 说明要继续收
                return
            elif ret > 0:
                # 收好了
                self._read_buffer = self._read_buffer[ret:]
                safe_call(self._on_read_complete, job_box)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. ret: %d, read_buffer: %r', ret, self._read_buffer)
                self._read_buffer = ''
                return

    def _on_read_complete(self, job_box):
        """
        完整数据接收完成
        :param job_box: 解析之后的job_box
        :return:
        """

        if job_box.cmd == constants.CMD_WORKER_TASK_DONE:
            self._on_job_end()

            # 如果有数据，就要先处理
            if job_box.body:
                # 要转发数据给原来的用户
                # 要求连接存在，并且连接还处于连接中
                if self._doing_job.client_conn and self._doing_job.client_conn.connected:
                    self._doing_job.client_conn.transport.write(job_box.body)

                    self.factory.proxy.stat_counter.client_rsp += 1

            self._try_alloc_job()

    def _try_alloc_job(self):
        # 无论有没有任务，都会标记自己空闲
        job = self.factory.proxy.job_dispatcher.alloc_job(self)
        if job:
            # 如果能申请成功，就继续执行
            self.assign_job(job)

    def assign_job(self, job):
        """
        分配任务
        :param job:
        :return:
        """
        self._doing_job = job
        # 发送
        self.transport.write(job.job_box.pack())
        self._on_job_begin()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

        if self._status == constants.WORKER_STATUS_IDLE:
            # 没有正在处理的任务
            self._doing_job = None
            self._job_begin_time = None

    def _on_job_begin(self):
        """
        当作业开始
        :return:
        """
        self.factory.proxy.stat_counter.worker_req += 1
        self._job_begin_time = time.time()

    def _on_job_end(self):
        """
        当作业结束
        :return:
        """
        now = time.time()
        past_time_ms = int((now - self._job_begin_time) * 1000)

        self.factory.proxy.stat_counter.add_job_time(past_time_ms)
        self.factory.proxy.stat_counter.worker_rsp += 1
