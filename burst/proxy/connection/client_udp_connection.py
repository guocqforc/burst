# -*- coding: utf-8 -*-

from twisted.internet.protocol import DatagramProtocol

from ...share.utils import safe_call
from ...share.log import logger
from ..task_container import TaskContainer
from ...share.task import Task
from ...share import constants


class ClientProtocol(DatagramProtocol):

    def __init__(self, proxy):
        self.proxy = proxy

    def datagramReceived(self, data, address):

        while data:
            box = self.proxy.app.box_class()
            ret = box.unpack(data)

            if ret == 0:
                # 说明要继续收
                logger.error('buffer incomplete. proxy: %s, ret: %d, read_buffer: %r',
                             self.proxy, ret, data)
                return
            elif ret > 0:
                # 收好了
                # 不能使用双下划线，会导致别的地方取的时候变为 _Gateway__raw_data，很奇怪
                box._raw_data = data[:ret]
                data = data[ret:]
                safe_call(self._on_read_complete, box)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. proxy: %s, ret: %d, read_buffer: %r',
                             self.factory.proxy, ret, data)
                data = ''
                return

    def _on_read_complete(self, box, address):
        self.proxy.stat_counter.client_req += 1

        conn = ClientConnection(self, address)

        # 获取映射的group_id
        group_id = self.factory.proxy.app.config['GROUP_ROUTER'](box)

        # 打包成内部通信的task
        task = Task(dict(
            cmd=constants.CMD_WORKER_TASK_ASSIGN,
            client_ip_num=self._client_ip_num,
            body=box._raw_data,
        ))

        task_container = TaskContainer(task, conn)
        self.proxy.task_dispatcher.add_task(group_id, task_container)

    def write(self, data, address):
        if self.transport:
            # 要求连接存在，并且连接还处于连接中
            self.transport.write(data, address)
            self.proxy.stat_counter.client_rsp += 1


class ClientConnection(object):

    protocol = None

    address = None

    def __init__(self, protocol, address):
        self.protocol = protocol
        self.address = address

    def write(self, data):
        """
        响应
        :return:
        """
        self.protocol.write(data, self.address)
        return True
