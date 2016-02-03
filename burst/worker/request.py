# -*- coding: utf-8 -*-


from ..proxy import JobBox
from .. import constants
from ..log import logger
from ..utils import ip_int_to_str


class Request(object):
    """
    请求
    """

    conn = None
    # 封装的传输box，外面不需要理解
    job_box = None
    box = None
    is_valid = False
    blueprint = None
    route_rule = None

    def __init__(self, conn, job_box):
        self.conn = conn
        self.job_box = job_box
        # 赋值
        self.is_valid = self._parse_raw_data()

    def _parse_raw_data(self):
        if not self.job_box.body:
            return True

        try:
            self.box = self.app.box_class()
        except Exception, e:
            logger.error('parse raw_data fail. e: %s, request: %s', e, self)
            return False

        if self.box.unpack(self.job_box.body) > 0:
            self._parse_route_rule()
            return True
        else:
            logger.error('unpack fail. request: %s', self)
            return False

    def _parse_route_rule(self):
        if self.cmd is None:
            return

        route_rule = self.app.get_route_rule(self.cmd)
        if route_rule:
            # 在app层，直接返回
            self.route_rule = route_rule
            return

        for bp in self.app.blueprints:
            route_rule = bp.get_route_rule(self.cmd)
            if route_rule:
                self.blueprint = bp
                self.route_rule = route_rule
                break

    @property
    def worker(self):
        return self.conn.worker

    @property
    def app(self):
        return self.worker.app

    @property
    def client_ip(self):
        """
        客户端连接IP，外面不需要了解job_box
        :return:
        """
        return ip_int_to_str(self.job_box.client_ip_num)

    @property
    def cmd(self):
        try:
            return self.box.cmd
        except:
            return None

    @property
    def view_func(self):
        return self.route_rule['view_func'] if self.route_rule else None

    @property
    def endpoint(self):
        if not self.route_rule:
            return None

        bp_endpoint = self.route_rule['endpoint']

        return '.'.join([self.blueprint.name, bp_endpoint] if self.blueprint else [bp_endpoint])

    def write(self, data):
        """
        写回，业务代码中请不要调用
        如果处理函数没有return数据的话，data可能为None，此时相当于直接进行ask_for_job
        :param data: 可以是dict也可以是box
        :return:
        """

        if isinstance(data, self.app.box_class):
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box.map(data).pack()

        job_box = JobBox(dict(
            cmd=constants.CMD_WORKER_TASK_DONE,
            body=data or '',
        ))

        return self.conn.write(job_box.pack())

    def __repr__(self):
        return 'cmd: %r, endpoint: %s, box: %r' % (self.cmd, self.endpoint, self.box)
