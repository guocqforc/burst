# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory, connectionDone

from burst.utils import safe_call
from burst.log import logger
from .. import constants


class WorkerConnectionFactory(Factory):

    def __init__(self, app, group_id):
        self.app = app
        self.group_id = group_id

    def buildProtocol(self, addr):
        return WorkerConnection(self, addr, self.group_id)


class WorkerConnection(Protocol):

    # 状态
    _status = None
    # 正在处理的任务
    _doing_task = None
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
        pass

    def connectionLost(self, reason=connectionDone):
        # 要删除掉对应的worker，因为不确定连接是否会及时释放
        # TODO，等测试一下，如果确定会自动释放的话，这代码就可以不用写了
        self.factory.app.proxy.task_dispatcher.remove_worker(self)

    def dataReceived(self, data):
        """
        当数据接受到时
        :param data:
        :return:
        """
        self._read_buffer += data

        while self._read_buffer:
            # 因为box后面还是要用的
            box = self.factory.app.box_class()
            ret = box.unpack(self._read_buffer)
            if ret == 0:
                # 说明要继续收
                return
            elif ret > 0:
                # 收好了
                box_data = self._read_buffer[:ret]
                self._read_buffer = self._read_buffer[ret:]
                safe_call(self._on_read_complete, box_data, box)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. ret: %d, read_buffer: %r', ret, self._read_buffer)
                self._read_buffer = ''
                return

    def _on_read_complete(self, data, box):
        """
        完整数据接收完成
        :param data: 原始数据
        :param box: 解析之后的box
        :return:
        """

        if box.cmd == constants.CMD_WORKER_ASK_FOR_JOB:
            # 说明是标记自己空闲
            task = self.factory.app.proxy.task_dispatcher.alloc_task(self)
            if task:
                # 如果能申请成功，就继续执行
                self.assign_task(task)
                return
        else:
            # 要转发数据给原来的用户
            # 要求连接存在，并且连接还处于连接中
            if self._doing_task.client_conn and self._doing_task.client_conn.connected:
                self._doing_task.client_conn.transport.write(data)

    def assign_task(self, task):
        """
        分配任务
        :param task:
        :return:
        """
        self._doing_task = task
        # 发送
        self.transport.write(task.raw_data)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

        if self._status == constants.WORKER_STATUS_IDLE:
            # 没有正在处理的任务
            self._doing_task = None
