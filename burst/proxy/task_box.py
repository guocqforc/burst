# -*- coding: utf-8 -*-

from netkit.box import Box
from collections import OrderedDict

# 如果header字段变化，那么格式也会变化
HEADER_ATTRS = OrderedDict([
    ('magic', ('i', 2037952207)),
    ('version', ('h', 0)),
    ('packet_len', ('i', 0)),
    ('cmd', ('i', 0)),
    ('client_ip_num', ('I', 0)),
    ])


class TaskBox(Box):
    header_attrs = HEADER_ATTRS

    @property
    def client_ip(self):
        """
        获取字符串格式的IP地址
        由于对端时间转为网络序的int存入进来，所以这里也要用网络序来pack
        字符串转int:
            struct.unpack("!I",socket.inet_aton(ip))[0]
        :return:
        """
        import socket
        import struct
        return socket.inet_ntoa(struct.pack("!I", self.client_ip_num))
