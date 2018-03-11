# coding=utf-8

from . import api
import logging
# 将来这里很有可能会用到db这个对象

# 这里发生了循环导包的问题, ihome没有执行完毕, 又需要ihome
# 如何解决: 让某些文件延迟加载
from ihome import db

from ihome import models

@api.route('/index')
def index():

    logging.error('error')
    logging.warn('warn')
    logging.info('info')
    logging.debug('debug')

    # Error: 错误级别
    # WARN: 警告级别
    # Info: 信息级别
    # Debug: 调试级别

    return 'index hello buleprint db 没有问题了'