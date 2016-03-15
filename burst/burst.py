# -*- coding: utf-8 -*-

import sys
import os
import json
from collections import Counter

from share.log import logger
from share.mixins import RoutesMixin, AppEventsMixin
from share import constants
from share.config import ConfigAttribute, Config
from share.utils import import_module_or_string


class Burst(RoutesMixin, AppEventsMixin):

    # 配置都放到 burst 里，而和proxy或者worker直接相关的类，则放到自己的部分
    ############################## configurable begin ##############################

    box_class = ConfigAttribute('BOX_CLASS',
                                get_converter=import_module_or_string)
    master_class = ConfigAttribute('MASTER_CLASS',
                                   get_converter=import_module_or_string)
    proxy_class = ConfigAttribute('PROXY_CLASS',
                                  get_converter=import_module_or_string)
    worker_class = ConfigAttribute('WORKER_CLASS',
                                   get_converter=import_module_or_string)

    debug = ConfigAttribute('DEBUG')

    ############################## configurable end   ##############################

    config = None
    blueprints = None

    def __init__(self):
        """
        构造函数
        :return:
        """
        RoutesMixin.__init__(self)
        AppEventsMixin.__init__(self)

        self.config = Config(defaults=constants.DEFAULT_CONFIG)
        self.blueprints = list()

    def register_blueprint(self, blueprint):
        blueprint.register_to_app(self)

    def run(self, host=None, port=None, debug=None):
        self._validate_cmds()

        if host is not None:
            self.config.update({
                'HOST': host,
            })

        if port is not None:
            self.config.update({
                'PORT': port,
            })

        if debug is not None:
            self.debug = debug

        # 只要没有这个环境变量，就是主进程
        str_burst_env = os.getenv(self.config['CHILD_PROCESS_ENV_KEY'])

        if not str_burst_env:
            # 主进程
            logger.info('Running server on %s:%s, debug: %s',
                        self.config['HOST'], self.config['PORT'], self.debug
                        )
            if self.config['ADMIN_ADDRESS']:
                logger.info('Running admin server on %s', self.config['ADMIN_ADDRESS'])
            self.master_class(self).run()
        else:
            burst_env = json.loads(str_burst_env)
            if burst_env['type'] == constants.PROC_TYPE_PROXY:
                # proxy
                self.proxy_class(self, self.config['HOST'], self.config['PORT']).run()
            else:
                # worker
                self.worker_class(self, burst_env['group_id']).run()

    def make_proc_name(self, subtitle):
        """
        获取进程名称
        :param subtitle:
        :return:
        """
        proc_name = '[%s:%s %s] %s' % (
            constants.NAME,
            subtitle,
            self.config['NAME'],
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

