# -*- coding: utf-8 -*-

import time

from twisted.internet.protocol import Protocol, Factory, connectionDone

from ...share.utils import safe_call
from ...share.log import logger
from ...share import constants
from ...share.task import Task


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
    _task_begin_time = None

    # 正在处理的任务
    _doing_task_container = None
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
        # 建立连接就直接去申请task
        self._try_alloc_task()

    def connectionLost(self, reason=connectionDone):
        # 要删除掉对应的worker
        self.factory.proxy.task_dispatcher.remove_worker(self)

    def dataReceived(self, data):
        """
        当数据接受到时
        :param data:
        :return:
        """
        self._read_buffer += data

        while self._read_buffer:
            # 因为box后面还是要用的
            task = Task()
            ret = task.unpack(self._read_buffer)
            if ret == 0:
                # 说明要继续收
                return
            elif ret > 0:
                # 收好了
                self._read_buffer = self._read_buffer[ret:]
                safe_call(self._on_read_complete, task)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. ret: %d, read_buffer: %r', ret, self._read_buffer)
                self._read_buffer = ''
                return

    def _on_read_complete(self, task):
        """
        完整数据接收完成
        :param task: 解析之后的task
        :return:
        """

        if task.cmd == constants.CMD_WORKER_TASK_DONE:
            self._on_task_end()

            # 如果有数据，就要先处理
            if task.body:
                # 要转发数据给原来的用户
                # 要求连接存在，并且连接还处于连接中
                if self._doing_task_container.client_conn and self._doing_task_container.client_conn.connected:
                    self._doing_task_container.client_conn.transport.write(task.body)

                    self.factory.proxy.stat_counter.client_rsp += 1

            self._try_alloc_task()

    def _try_alloc_task(self):
        # 无论有没有任务，都会标记自己空闲
        task_container = self.factory.proxy.task_dispatcher.alloc_task(self)
        if task_container:
            # 如果能申请成功，就继续执行
            self.assign_task(task_container)

    def assign_task(self, task_container):
        """
        分配任务
        :param task_container:
        :return:
        """
        self._doing_task_container = task_container
        # 发送
        self.transport.write(task_container.task.pack())
        self._on_task_begin()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

        if self._status == constants.WORKER_STATUS_IDLE:
            # 没有正在处理的任务
            self._doing_task_container = None
            self._task_begin_time = None

    def _on_task_begin(self):
        """
        当作业开始
        :return:
        """
        self.factory.proxy.stat_counter.worker_req += 1
        self._task_begin_time = time.time()

    def _on_task_end(self):
        """
        当作业结束
        :return:
        """
        now = time.time()
        past_time_ms = int((now - self._task_begin_time) * 1000)

        self.factory.proxy.stat_counter.add_task_time(past_time_ms)
        self.factory.proxy.stat_counter.worker_rsp += 1
