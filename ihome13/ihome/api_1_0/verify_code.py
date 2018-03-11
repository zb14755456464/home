# coding=utf-8

import logging
import random
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from ihome.response_code import RET
from flask import jsonify, make_response, request
from ihome.models import User
from ihome.libs.yuntongxin.sms import CCP
from ihome import constants

# 图形验证码 & 短信验证接口

# /api/v1_0/image_codes


# image_codes--> 符合第三四条 : 只需要名词变复数 /  获取单个商品需要/后加id
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):

    # 生成了验证码
    name, text, image_data = captcha.generate_captcha()

    # 保存到redis中 setex: 可以设置数据并设置有效期
    # 需要三个参数: key , expiretime, value

    try:
        redis_store.setex('image_code_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 需要存储到日志文件中去
        logging.error(e)

        # 需要返回JSON数据, 以键值对返回
        resp = {
            'errno': RET.DBERR,
            'errmsg': '保存验证码失败'
        }
        return jsonify(resp)

    # 返回响应数据
    resp = make_response(image_data)
    resp.headers['Content-Type'] = 'image/jpg'

    return resp


"""
这里使用手机号当做id, 可以通过正则来过滤一些垃圾请求
GET /api/v1_0/sms_codes/17612345678?image_code=werz&image_code_id=61242
用户填写的验证码
用户的手机号
图像验证码的编码
"""

@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def send_sms_code(mobile):

    # 一. 获取参数
    # mobile
    # imaga_code
    # image_code_id
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    # 二. 验证参数的完整性及有效性
    if not all([image_code, image_code_id]):
        resp_dict = {
            'errno': RET.PARAMERR,
            'errmsg': '参数不完整'
        }
        return jsonify(resp_dict)

    # 三. 处理业务逻辑

    # 1. try: 从redis中获取真实的图片验证码
    try:
        real_image_code = redis_store.get('image_code_' + image_code_id)
    except Exception as e:
        # 保存错误日志
        logging.error(e)
        # 返回错误信息
        resp_dict = {
            'errno': RET.DBERR,
            'errmsg': '获取图片验证码失败'
        }
        return jsonify(resp_dict)

    # 2. 判断图像验证码是否过期
    # 一般从数据库中获取了一个空值NULL 就是None
    if real_image_code is None:
        # 返回错误信息
        resp_dict = {
            'errno': RET.NODATA,
            'errmsg': '图片验证码过期/失效'
        }
        return jsonify(resp_dict)

    # 3. try:无论验证成功与否, 都执行删除redis中的图形验证码
    try:
        redis_store.delete('image_code_' + image_code_id)
    except Exception as e:
        logging.error(e)
        # 一般来说, 只要是删除数据库出错, 都不应该返回错误信息. 因为这个操作, 不是用户做错了
        # 此时, 只需要记录日志即可


    # 4. 判断用户填写的验证码与真实验证码是否一致, 需要转换小(大)写后在比较
    if real_image_code.lower() != image_code.lower():
        resp_dict = {
            'errno': RET.DATAERR,
            'errmsg': '图片验证码填写有误'
        }
        return jsonify(resp_dict)


    # 5. try:判断用户手机号是否注册过--> 在短信发送之前, 节省资源
    try:
        user = User.query.filter_by(mobile = mobile).first()
    except Exception as e:
        logging.error(e)
        # 理论上应该返回错误信息, 但是注册的时候还需要去验证, 去获取数据库.
        # 因此, 考虑到用户体验, 我们这一次就放过去, 让用户先接受验证码, 知道注册的时候再去判断
    else:
        # 如果查询成功, 再次判断user是否存在
        # 如果数据库没有数据, 返回一个NULL --> None
        if user is not None:
            resp_dict = {
                'errno': RET.DATAEXIST,
                'errmsg': '手机号已注册, 直接登录即可'
            }
            return jsonify(resp_dict)


    # 6. 创建/生成6位验证码
    sms_code = '%06d' % random.randint(0, 999999)

    # 7. try:将短信验证码保存redis中
    try:
        # 保存到redis中 setex: 可以设置数据并设置有效期
        # 需要三个参数: key , expiretime, value
        redis_store.setex('sms_code_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        logging.error(e)
        resp_dict = {
            'errno': RET.DBERR,
            'errmsg': '保存验证码异常'
        }
        return jsonify(resp_dict)


    # 8. try:发送验证码
    try:
        ccp = CCP()
        # 第一个是手机号, 第二个发短信模板需要的参数[验证码, 过期时间], 第三个短信的模板编号
        # result 如果发送短信成功, 就会返回0, 如果失败,就会返回-1
        result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    except Exception as e:
        logging.error(e)
        resp_dict = {
            'errno': RET.THIRDERR,
            'errmsg': '发送短信异常'
        }
        return jsonify(resp_dict)



    # 四. 返回数据
    if result == 0:
        # 0, 表示发送短信成功
        resp_dict = {
            'errno': RET.OK,
            'errmsg': '发送短信成功'
        }
        return jsonify(resp_dict)
    else:
        # -1, 表示发送短信失败
        resp_dict = {
            'errno': RET.THIRDERR,
            'errmsg': '发送短信失败'
        }
        return jsonify(resp_dict)


























