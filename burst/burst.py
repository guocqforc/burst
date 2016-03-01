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
    ############################## configurable begin ##############################

    # 进程名字
    name = constants.NAME

    box_class = None
    group_conf = None
    group_router = None

    # proxy的backlog
    proxy_backlog = constants.PROXY_BACKLOG

    # worker<->proxy网络连接超时(秒)
    worker_conn_timeout = constants.WORKER_CONN_TIMEOUT
    # 处理task超时(秒). 超过后worker会自杀. None 代表永不超时
    work_timeout = None

    # 停止子进程超时(秒). 使用 TERM 进行停止时，如果超时未停止会发送KILL信号
    stop_timeout = None
    # proxy<->worker之间通信的address模板
    ipc_address_tpl = constants.IPC_ADDRESS_TPL

    # 管理员，可以连接proxy获取数据
    # 管理员访问地址如 (127.0.0.1, 22222)
    admin_address = None
    admin_username = None
    admin_password = None

    # 统计相关
    # 作业时间统计标准
    tasks_time_benchmark = constants.TASKS_TIME_BENCHMARK

    ############################## configurable end   ##############################

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

        self.blueprints = list()

    def register_blueprint(self, blueprint):
        blueprint.register_to_app(self)

    def run(self, host, port):
        self._validate_cmds()

        # 只要没有这个环境变量，就是主进程
        str_burst_env = os.getenv(constants.CHILD_ENV_KEY)

        if not str_burst_env:
            # 主进程
            logger.info('Running server on %s:%s', host, port)
            if self.admin_address:
                logger.info('Running admin server on %s:%s', self.admin_address[0], self.admin_address[1])
            Master(self).run()
        else:
            burst_env = json.loads(str_burst_env)
            if burst_env['type'] == constants.PROC_TYPE_PROXY:
                # proxy
                Proxy(self, host, port).run()
            else:
                # worker
                Worker(self, burst_env['group_id']).run()

    def make_proc_name(self, subtitle):
        """
        获取进程名称
        :param subtitle:
        :return:
        """
        proc_name = '[%s %s:%s] %s' % (
            self.name,
            constants.NAME,
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

