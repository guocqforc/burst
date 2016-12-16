# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')

import socket
from netkit.box import Box

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

box = Box()
box.cmd = 1
# box.cmd = 101
box.body = '我爱你'

sock.sendto(box.pack(), ('127.0.0.1', 9900))

while True:
    data, address = sock.recvfrom(1000)

    recv_box = Box()
    recv_box.unpack(data)

    print recv_box
