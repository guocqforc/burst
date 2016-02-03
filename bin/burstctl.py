#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import argparse
from netkit.box import Box
from netkit.contrib.tcp_client import TcpClient
from burst import constants


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--host', help='burst admin host', action='store', default='127.0.0.1')
    parser.add_argument('-P', '--port', type=int, help='burst admin port', action='store', required=True)
    parser.add_argument('-u', '--username', help='username', action='store', default=None)
    parser.add_argument('-p', '--password', help='password', action='store', default=None)
    parser.add_argument('-c', '--cmd', type=int, help='cmd', action='store', default=constants.CMD_ADMIN_SERVER_STAT)
    parser.add_argument('-o', '--timeout', type=int, help='connect/send/receive timeout', action='store', default=10)
    return parser


def run():
    global debug

    args = build_parser().parse_args()

    tcp_client = TcpClient(Box, args.host, args.port, args.timeout)

    try:
        tcp_client.connect()
    except Exception, e:
        print 'connect fail: ', e
        return

    box = Box(dict(
        cmd=args.cmd,
        body=json.dumps(
            dict(
                auth=dict(
                    username=args.username,
                    password=args.password,
                )
            )
        )
    ))

    tcp_client.write(box)

    rsp_box = tcp_client.read()

    if rsp_box.ret != 0:
        print 'fail. rsp_box.ret=%s' % rsp_box.ret
        return
    else:
        print json.loads(rsp_box.body)


if __name__ == '__main__':
    run()

