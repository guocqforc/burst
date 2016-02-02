# -*- coding: utf-8 -*-

import sys
import os
import json
from collections import Counter
from log import logger
from mixins import RoutesMixin, AppEventsMixin
import constants
from proxy import Proxy
from worker import Worker
from master import Master


class Burst(RoutesMixin, AppEventsMixin):

    # 配置都放到 burst 里，而和proxy或者worker直接相关的类，则放到自己的部分

    # 进程名字
    name = constants.NAME

    box_class = None
    proxy_backlog = constants.PROXY_BACKLOG

    group_conf = None
    group_router = None

    # 网络连接超时(秒)
    conn_timeout = constants.CONN_TIMEOUT
    # 处理job超时(秒). 超过后worker会自杀. None 代表永不超时
    job_timeout = None
    # 停止子进程超时(秒). 使用 TERM / USR1 进行停止时，如果超时未停止会发送KILL信号
    stop_timeout = None
    # proxy<->worker之间通信的address模板
    ipc_address_tpl = constants.IPC_ADDRESS_TPL

    master = None
    proxy = None
    worker = None
    blueprints = None

    def __init__(self, box_class, group_conf, group_router):
        """
        构造函数
        :param box_class: box类
        :param group_conf: 进程配置，格式如下:
            {
                $group_id: {
                    count: 10,
                }
            }
        :param group_router: 通过box路由group_id:
            def group_router(box):
                return group_id
        :return:
        """
        RoutesMixin.__init__(self)
        AppEventsMixin.__init__(self)

        self.box_class = box_class
        self.group_conf = group_conf
        self.group_router = group_router

        self.master = Master(self)
        self.proxy = Proxy(self)
        self.worker = Worker(self)
        self.blueprints = list()

    def register_blueprint(self, blueprint):
        blueprint.register_to_app(self)

    def run(self, host=None, port=None):
        self._validate_cmds()

        # 只要没有这个环境变量，就是主进程
        str_burst_env = os.getenv(constants.CHILD_ENV_KEY)

        if not str_burst_env:
            # 主进程
            logger.info('Running server on %s:%s', host, port)
            self.master.run()
        else:
            burst_env = json.loads(str_burst_env)
            if burst_env['type'] == constants.PROC_TYPE_PROXY:
                # proxy
                self.proxy.run(host, port)
            else:
                # worker
                self.worker.run(burst_env['group_id'])

    def make_proc_name(self, subtitle):
        """
        获取进程名称
        :param subtitle:
        :return:
        """
        proc_name = '[%s:%s] %s' % (
            self.name,
            subtitle,
            ' '.join([sys.executable] + sys.argv)
        )

        return proc_name

    def _validate_cmds(self):
        """
        确保 cmd 没有重复
        :return:
        """

        cmd_list = list(self.rule_map.keys())

        for bp in self.blueprints:
            cmd_list.extend(bp.rule_map.keys())

        duplicate_cmds = (Counter(cmd_list) - Counter(set(cmd_list))).keys()

        assert not duplicate_cmds, 'duplicate cmds: %s' % duplicate_cmds

