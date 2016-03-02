# -*- coding: utf-8 -*-

import socket
from netkit.stream import Stream


class UnixClient(object):
    """
    封装过的unix socket client
    """

    box_class = None
    stream_checker = None
    address = None
    timeout = None
    stream = None

    def __init__(self, box_class, address, timeout=None):
        self.box_class = box_class
        self.address = address
        self.timeout = timeout
        self.stream_checker = self.box_class().check

    def connect(self):
        """
        连接服务器，失败会抛出异常
        :return:
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.address)
        except Exception, e:
            sock.close()
            raise e

        self.stream = Stream(sock)

    def read(self):
        """
        如果超时会抛出异常 socket.timeout
        :return:
        """
        if self.closed():
            return None

        data = self.stream.read_with_checker(self.stream_checker)
        if not data:
            return None

        box = self.box_class()
        box.unpack(data)

        return box

    def write(self, data):
        """
        写入
        :param data:
        :return:    True/False
        """
        if self.closed():
            return False

        if isinstance(data, self.box_class):
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box_class(data).pack()

        return self.stream.write(data)

    def close(self):
        if not self.stream:
            return

        return self.stream.close()

    def closed(self):
        if not self.stream:
            return True

        return self.stream.closed()

    def __str__(self):
        return 'box_class: %s, address: %s, timeout: %s' % (self.box_class, self.address, self.timeout)
