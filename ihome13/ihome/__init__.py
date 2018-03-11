# coding=utf-8

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from config import config_dict
import redis
import logging
from logging.handlers import RotatingFileHandler
from utils.commons import RegexConverter

# 为了外界调用, 需要先定义db, 但是不能初始化, 延迟加载(app创建后, 调用init加载)
db = SQLAlchemy()

# 定义CSRF对象
csrf = CSRFProtect()

# 定义redis_store对象, 先设置为None
redis_store = None



"""
开发时, 为了调试方便, 会打印很多参数, 查看数据是否正确
上线后, 用户不需要关心, 只需要记录错误日志即可
代码不需要删除, 但是可以有选择性的输出
"""


logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日后记录器
logging.getLogger().addHandler(file_log_handler)


# 提供一个创建app的方法, 一次性创建所有需要的对象, 方便manage进行调用
def create_app(config_name):

    app = Flask(__name__)

    # app.url_map.converters['re'] 里面的re, 就是将来要使用的key, 随便写
    # 以后就可以使用re. 来实现之前定义的正则了
    app.url_map.converters['re'] = RegexConverter

    # 从配置文件的字典中, 传入参数名字, 获取配置对象
    config = config_dict[config_name]

    app.config.from_object(config)

    # 创建数据库
    db.init_app(app)

    # 创建CSRF对象
    csrf.init_app(app)

    # 创建redis
    global redis_store
    redis_store = redis.StrictRedis(port=config.REDIS_PORT,host=config.REDIS_HOST)

    # 创建Session, 将session数据从以前默认的cookie, 存放到redis中
    # http://pythonhosted.org/Flask-Session/ 教程
    Session(app)

    # 用到的时候在导包  ImportError: cannot import name db
    from ihome.api_1_0 import api
    # 注册蓝图, 为了符合RESTFUl风格, 需要增加url前缀
    app.register_blueprint(api, url_prefix = '/api/v1_0')

    import web_html
    app.register_blueprint(web_html.html)


    return app
