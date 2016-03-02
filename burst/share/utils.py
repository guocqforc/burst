# -*- coding: utf-8 -*-

import functools

from log import logger


def safe_call(func, *args, **kwargs):
    """
    安全调用
    """
    try:
        return func(*args, **kwargs)
    except Exception, e:
        logger.error('exc occur. e: %s, func: %s', e, func, exc_info=True)
        # 调用方可以通过 isinstance(e, BaseException) 来判断是否发生了异常
        return e


def safe_func(func):
    """
    把函数变为安全的
    """
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        return safe_call(func, *args, **kwargs)
    return func_wrapper


def ip_int_to_str(ip_num):
    """
    转换ip格式，从int转为str
    :param ip_num:
    :return:
    """
    import socket
    import struct
    return socket.inet_ntoa(struct.pack("!I", ip_num))


def ip_str_to_int(ip_str):
    """
    转化ip格式，从str转为int
    :param ip_str:
    :return:
    """
    import socket
    import struct

    return struct.unpack("!I", socket.inet_aton(ip_str))[0]


def parse_address_uri(uri):
    """
    解析uri为可用的address，目前只检测 tcp 和 unix
    :param uri: tcp://127.0.0.1:5555, unix:///data/release/ipc.sock
    :return: (socket_type, address)
    """
    import re
    import socket

    result = re.match(r'(\w+)://(.*)', uri)

    if len(result.groups()) != 2:
        # 说明失败了
        return None, None

    if result.group(1) == 'tcp':
        host, port = result.group(2).split(':')
        port = int(port)
        return socket.AF_INET, (host, port)

    elif result.group(1) == 'unix':
        return socket.AF_UNIX, result.group(2)

    else:
        return None, None

