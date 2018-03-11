# coding=utf-8

import logging
from . import api
from ihome.utils.commons import login_required
from flask import request, g, jsonify, current_app, session
from ihome.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import constants, db


@api.route('/users/avatar', methods=["POST"])
@login_required
def set_user_avatar():

    # 图片是以表单提交的

    # 一. 获取数据
    # 1.1 获取用户的ID
    user_id = g.user_id

    # 1.2 获取头像对象
    image_file = request.files.get('avatar')

    # 二. 效验参数
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图像')

    # 三. 业务处理
    # 保存图像 --> 1. 七牛云 2. MySql
    # 3.1 读取图片的二进制数据
    image_data = image_file.read()

    # 3.2 try:保存七牛云
    try:
        # file_name 就存储的是图片名. 将来就可以再程序中调用显示
        file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图像异常')

    # 3.3 try:保存图像到数据库中
    try:
        # update: 查询之后拼接update, 可以直接进行更新操作, 不需要在执行提交操作
        # update中需要传入字典
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库保存图像失败')

    # 四. 返回值

    # 此时的文件名, 没有域名. 因此如果直接返回给客户端, 客户端无法直接加载
    # ozcxm6oo6.bkt.clouddn.com
    # 为了避免在数据库存储过多重复的域名前缀, 因此保存的时候, 不加域名. 返回给前端数据时, 我们拼接域名即可

    # 拼接完整的图像URL地址
    avatar_url = constants.QINIU_URL_DOMAIN + file_name

    # 返回的时候, 记得添加图像url信息
    # 如果还需要额外的返回数据, 可以再后方自行拼接数据, 一般会封装成一个字典返回额外数据
    return jsonify(errno=RET.OK, errmsg='保存图像成功', data={"avatar_url": avatar_url})


@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    # 使用了login_required装饰器后，可以从g对象中获取用户user_id
    user_id = g.user_id

    # 获取用户想要设置的用户名
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    name = req_data.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="设置用户错误")

    # 修改session数据中的name字段
    session["user_name"] = name
    return jsonify(errno=RET.OK, errmsg="OK", data={"name": name})


@api.route("/users", methods=["GET"])
@login_required
def get_user_profile():
    """获取个人信息"""
    user_id = g.user_id
    # 查询数据库获取个人信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户 的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 保存用户的姓名与身份证号
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None)\
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

    return jsonify(errno=RET.OK, errmsg="OK")
