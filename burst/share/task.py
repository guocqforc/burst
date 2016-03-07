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


class Task(Box):
    header_attrs = HEADER_ATTRS
