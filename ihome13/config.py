# coding=utf-8

import redis

# 配置数据库地址, redis端口等参数, 以及调试模式/开发模式

class Config(object):

    # flask-sqlalchemy使用的参数
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1/ihome13"  # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = True  # 追踪数据库的修改行为，如果不设置会报警告，不影响代码的执行
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # 配置redis的数据
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 配置session存储到redis中
    SECRET_KEY = 'jlhqsDJKREWASDFGJKLNSALFJKLHNSLJFKHGNLMSW'
    PERMANENT_SESSION_LIFETIME = 86400 # 单位是秒, 设置session过期的时间
    SESSION_TYPE = 'redis' # 指定存储session的位置为redis
    SESSION_USE_SIGNER = True # 对数据进行签名加密, 提高安全性
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 设置redis的ip和端口

class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass

# 参数字典, 用来方便的加载调试模式
config_dict = {
    'development' : DevelopmentConfig,
    'production' : ProductionConfig
}
