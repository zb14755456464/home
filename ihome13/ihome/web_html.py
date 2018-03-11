# coding=utf-8

from flask import Blueprint, current_app, make_response
from flask_wtf.csrf import generate_csrf

html = Blueprint('html', __name__)

# @html.route('/')
# def get_index():
#     return 'index'

# 此时如果访问跟路由, 下面的路由是进不去的. 因此系统自带的匹配规则我们不需要. 需要我们自定义正则的匹配规则
"""
1. 继承BaseConvert类
2. 自定义一个转换类
3. 给app.urlmap增加自定义的过滤器
"""

# 127.0.0.1:5000/
# 127.0.0.1:5000/index.html


# r 表示使用原始字符串, 不需要转义
# . 表示任意字符串, 除了换行
# * 表示匹配0次或多次
@html.route("/<re(r'.*'):file_name>")
def get_html_file(file_name):


    # 返回的时候, 直接返回静态的html页面. 把页面当做静态资源返回. 而不是通过渲染模板的方式
    # 只要调用了send_static_file方法, 就会从static目录下去匹配()的路径的文件
    # current_app 就是 创建之后的app

    # 1. 根路由
    if not file_name:
        file_name = 'index.html'

    # 2. 处理网页左上角的图标 --> 如果发现file_name = favicon.ico, 就直接返回
    # 默认都会在static中, 有一个"favicon.ico", 当做图标. 这个请求是默认就会发送的

    if file_name != 'favicon.ico':
        file_name = 'html/' + file_name
    print file_name

    # 我们增加了csrf保护, 就需要手动将csrf_token, 给客户端的cookie

    # 生成随机的csrf_token
    csrf_token = generate_csrf()
    resp = make_response(current_app.send_static_file(file_name))
    resp.set_cookie('csrf_token', csrf_token)

    return resp


























