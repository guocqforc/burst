# -*- coding: utf-8 -*-

"""
从haven拿过来的
"""

import threading
from utils import safe_call


class ThreadTimer(object):

    timer = None

    def set(self, interval, callback, repeat=False, force=True):
        """
        添加timer
        """
        if self.timer:
            if force:
                # 如果已经存在，那么先要把现在的清空
                self.clear()
            else:
                # 已经存在的话，就返回了
                return

        def callback_wrapper():

            # 必须要确定，这次调用就是这个timer引起的
            if self.timer == timer:
                self.timer = None
                result = safe_call(callback)
                if repeat and not self.timer:
                    # 之所以还要判断timer，是因为callback中可能设置了新的回调
                    self.set(interval, callback, repeat, True)
                return result

        self.timer = timer = threading.Timer(interval, callback_wrapper)
        # 跟着主线程结束。默认值是和创建的线程一致
        timer.daemon = True
        timer.start()

    def is_set(self):
        """
        是否被设置了timer
        """
        return self.timer is not None

    def clear(self):
        """
        直接把现在的清空
        """
        if not self.timer:
            return

        try:
            self.timer.cancel()
        except:
            pass
        self.timer = None
