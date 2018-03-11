# coding=utf-8

# 一些公用的工具类放到这里

from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from functools import wraps
from ihome.response_code import RET

class RegexConverter(BaseConverter):
    # url_map路由映射字典
    def __init__(self, url_map, regex):
        # regex: 就是路由里的正则表达式. 目前只有一个, 因此也可以用regex来表示
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex



# 目的: 在每一个需要判断是否登录的方法之前, 先调用我们下面的方法, 来判断用户是否登录过
# view_func --> logout

def login_required(view_func):
    """检验用户的登录状态"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            # 表示用户已经登录
            # 使用g对象保存user_id，在视图函数中可以直接使用
            # 比如后面设置头像的时候, 仍然需要获取session的数据. 为了避免多次访问redis服务器. 可以使用g变量
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 用户未登录
            resp = {
                "errno": RET.SESSIONERR,
                "errmsg": "用户未登录"
            }
            return jsonify(resp)
    return wrapper