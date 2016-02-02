# -*- coding: utf-8 -*-


class Request(object):
    """
    请求
    """

    conn = None
    box = None
    blueprint = None
    # 是否已经作出回应
    responded = False
    route_rule = None

    def __init__(self, conn, box):
        self.conn = conn
        self.box = box
        self._parse_route_rule()

    @property
    def worker(self):
        return self.conn.worker

    @property
    def app(self):
        return self.worker.app

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
        写回
        :param data: 可以是dict也可以是box
        :return:
        """

        if isinstance(data, self.app.box_class):
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box.map(data).pack()

        succ = self.conn.write(data)
        if succ:
            # 如果发送成功，就标记为已经回应
            self.responded = True

        return succ

    def __repr__(self):
        return 'cmd: %r, endpoint: %s, box: %r' % (self.cmd, self.endpoint, self.box)
