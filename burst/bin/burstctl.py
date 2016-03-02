#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import click
from collections import OrderedDict
from netkit.box import Box
from netkit.contrib.tcp_client import TcpClient
from burst import constants


class BurstCtl(object):

    host = None
    port = None
    timeout = None
    username = None
    password = None

    tcp_client = None

    def __init__(self, host, port, timeout, username, password, extra=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password

    def make_send_box(self, cmd, username, password):
        return Box(dict(
            cmd=cmd,
            body=json.dumps(
                dict(
                    auth=dict(
                        username=username,
                        password=password,
                    )
                )
            )
        ))

    def output(self, s):
        print '/' + '-' * 80
        print s
        print '-' * 80 + '/'

    def _handle_stat_once(self):
        send_box = self.make_send_box(constants.CMD_ADMIN_SERVER_STAT, self.username, self.password)
        self.tcp_client.write(send_box)

        rsp_box = self.tcp_client.read()

        if not rsp_box:
            self.output('disconnected.')
            return False

        if rsp_box.ret != 0:
            self.output('fail. rsp_box.ret=%s' % rsp_box.ret)
            return False

        body_dict = json.loads(rsp_box.body)

        output_items = []
        for key in ('clients', 'busy_workers', 'idle_workers', 'pending_tasks',
                    'client_req', 'client_rsp', 'worker_req', 'worker_rsp'):

            output_items.append((key, body_dict.get(key)))

        def tasks_time_cmp_func(item1, item2):
            k1 = item1[0]
            k2 = item2[0]
            if k1 == 'more':
                return 1
            if k2 == 'more':
                return -1

            return cmp(int(k1), int(k2))

        tasks_time_items = sorted(body_dict['tasks_time'].items(), cmp=tasks_time_cmp_func)

        output_items.append(('tasks_time', OrderedDict(tasks_time_items)))

        output_dict = OrderedDict(output_items)

        # OrderedDict在通过json打印的时候，会保持原来的顺序
        self.output(json.dumps(output_dict, indent=4))

        return True

    def start(self):
        self.tcp_client = TcpClient(Box, self.host, self.port, self.timeout)

        try:
            self.tcp_client.connect()
        except Exception, e:
            self.output('connect fail: %s' % e)
            return False

        return True

    def handle_stat(self, loop):
        """
        :param loop:
        :return:
        """
        loop_times = 0

        while True:

            result = self._handle_stat_once()

            if not result:
                break

            loop_times += 1
            if loop_times >= loop > 0:
                break

            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break


def send_and_recv(tcp_client, box):
    tcp_client.write(box)

    rsp_box = tcp_client.read()

    if not rsp_box:
        print 'disconnected.'
        return False

    if rsp_box.ret != 0:
        print 'fail. rsp_box.ret=%s' % rsp_box.ret
        return False
    else:
        print '/' + '-' * 80
        print json.dumps(json.loads(rsp_box.body), indent=4)
        print '-' * 80 + '/'
        return True


@click.group()
def cli():
    pass


@cli.command()
@click.option('-t', '--host', help='burst admin host', default='127.0.0.1')
@click.option('-P', '--port', type=int, help='burst admin port', required=True)
@click.option('-o', '--timeout', type=int, help='connect/send/receive timeout', default=10)
@click.option('-u', '--username', help='username', default=None)
@click.option('-p', '--password', help='password', default=None)
@click.option('-l', '--loop', type=int, help='loop times, <=0 means infinite loop', default=-1)
def stat(host, port, timeout, username, password, loop):
    ctl = BurstCtl(host, port, timeout, username, password)
    ctl.start()
    ctl.handle_stat(loop)


if __name__ == '__main__':
    cli()
