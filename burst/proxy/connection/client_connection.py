# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory, connectionDone

from ...share.utils import safe_call, ip_str_to_int
from ...share.log import logger
from ..task_container import TaskContainer
from ...share.task import Task
from ...share import constants


class ClientConnectionFactory(Factory):

    def __init__(self, proxy):
        self.proxy = proxy

    def buildProtocol(self, addr):
        return ClientConnection(self, addr)


class ClientConnection(Protocol):
    _read_buffer = None

    # 客户端IP的数字
    _client_ip_num = None

    def __init__(self, factory, address):
        self.factory = factory
        self.address = address
        self._read_buffer = ''

    def connectionMade(self):

        self.factory.proxy.stat_counter.clients += 1

        # 转换string为int
        self._client_ip_num = ip_str_to_int(self.transport.client[0])

    def connectionLost(self, reason=connectionDone):

        self.factory.proxy.stat_counter.clients -= 1

    def dataReceived(self, data):
        """
        当数据接受到时
        :param data:
        :return:
        """
        self._read_buffer += data

        while self._read_buffer:
            # 因为box后面还是要用的
            box = self.factory.proxy.app.box_class()
            ret = box.unpack(self._read_buffer)
            if ret == 0:
                # 说明要继续收
                return
            elif ret > 0:
                # 收好了
                # 不能使用双下划线，会导致别的地方取的时候变为 _Gateway__raw_data，很奇怪
                box._raw_data = self._read_buffer[:ret]
                self._read_buffer = self._read_buffer[ret:]
                safe_call(self._on_read_complete, box)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. ret: %d, read_buffer: %r', ret, self._read_buffer)
                self._read_buffer = ''
                return

    def _on_read_complete(self, box):
        """
        完整数据接收完成
        :param box: 解析之后的box
        :return:
        """
        self.factory.proxy.stat_counter.client_req += 1

        # 获取映射的group_id
        group_id = self.factory.proxy.app.config['GROUP_ROUTER'](box)

        # 打包成内部通信的task
        task = Task(dict(
            cmd=constants.CMD_WORKER_TASK_ASSIGN,
            client_ip_num=self._client_ip_num,
            body=box._raw_data,
        ))

        task_container = TaskContainer(task, self)
        self.factory.proxy.task_dispatcher.add_task(group_id, task_container)
