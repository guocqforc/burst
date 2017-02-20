# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory, connectionDone


class MasterConnectionFactory(Factory):

    def __init__(self, proxy):
        self.proxy = proxy

    def buildProtocol(self, addr):
        return MasterConnection(self, addr)


class MasterConnection(Protocol):

    def __init__(self, factory, address):
        self.factory = factory
        self.address = address

    def connectionMade(self):
        self.factory.proxy.master_conn = self

    def connectionLost(self, reason=connectionDone):
        if self.factory.proxy.master_conn == self:
            self.factory.proxy.master_conn = None

    def dataReceived(self, data):
        """
        当数据接受到时，暂时不用处理
        :param data:
        :return:
        """
        pass
