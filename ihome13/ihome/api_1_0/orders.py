# coding=utf-8
# 导入日期模块，用来格式化日期数据
import datetime
# 导入flask内置的模块
from flask import request, g, jsonify, current_app
# 导入数据库实例
from ihome import db, redis_store
# 导入登陆验证装饰器
from ihome.utils.commons import login_required
# 导入自定义状态码
from ihome.response_code import RET
# 导入模型类
from ihome.models import House, Order
# 导入蓝图
from . import api


@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """保存订单"""
    # 一. 获取数据
    # 获取用户id
    user_id = g.user_id
    # 获取参数,校验参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 进一步获取详细参数信息,house_id/start_date/end_date
    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")

    # 二. 校验参数完整性
    # 2.1 完整性校验
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2.2 对日期格式化,datetime
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        # 断言订单天数至少1天
        assert start_date <= end_date
        # 计算预订的天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

    # 三. 业务逻辑处理
    # 3.1 查询房屋是否存在
    try:
        # House.query.filter_by(id=house_id).first()
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")
    # 校验查询结果
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 3.2 判断用户是否为房东
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="不能预订自己的房屋")

    # 3.3 查询是否被别人预定
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="检查出错，请稍候重试")
    # 校验查询结果
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已被预订")

    # 3.4 计算房屋总价
    amount = days * house.price
    # 生成模型类对象,保存订单基本信息:房屋/用户/订单的开始日期/订单的结束日期/天数/价格/总价
    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount
    #　3.5 保存订单数据到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 提交数据如果发生异常,需要进行回滚操作
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    # 四. 返回数据
    # 前端对应服务器的操作如果是更新资源或新建资源,可以返回对应的信息,
    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


@api.route("/users/orders", methods=["GET"])
@login_required
def get_user_orders():
    """查询用户的订单信息"""
    # 一. 获取数据
    user_id = g.user_id

    # 用户的身份，用户想要查询作为房客预订别人房子的订单，还是想要作为房东查询别人预订自己房子的订单
    role = request.args.get("role", "")

    # 二. 业务逻辑处理
    # 2.1 查询订单数据
    try:
        if "landlord" == role:
            # 以房东的身份查询订单
            # 先查询属于自己的房子有哪些
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # 再查询预订了自己房子的订单,默认按照房屋订单发布时间进行倒叙排序
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        else:
            # 以房客的身份查询订单， 查询自己预订的订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")

    # 2.2 将订单对象转换为字典数据
    orders_dict_list = []
    # 校验查询结果
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    # 三. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """接单、拒单"""
    # 一. 获取数据
    # 获取用户信息
    user_id = g.user_id
    # 获取参数,校验参数存在
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # action参数表明客户端请求的是接单还是拒单的行为
    action = req_data.get("action")

    # 二. 校验完整性
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 三. 业务逻辑处理
    # 3.1 获取订单的状态信息
    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        # 查询所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    # 3.2 确保房东只能修改属于自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    # 3.3 对接单或拒单分别做处理
    # 如果房东选择接单操作
    if action == "accept":
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_COMMENT"
    # 如果房东选择拒单操作，需要填写拒单原因
    elif action == "reject":
        # 拒单，要求用户传递拒单原因
        reason = req_data.get("reason")
        # 判断房东是否填写拒单原因
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 如果房东选择拒单,把拒单原因存如数据库,
        order.status = "REJECTED"
        # comment字段保存拒单原因
        order.comment = reason

    # 3.4 把接单或拒单操作存储数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 写入数据如果发生异常,进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    #四. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """保存订单评论信息"""
    # 一. 获取数据
    user_id = g.user_id
    # 获取参数
    req_data = request.get_json()
    # 尝试获取评价内容
    comment = req_data.get("comment")

    # 二. 校验参数
    # 要求用户必须填写评论内容
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 三. 业务逻辑处理
    # 3.1 查询订单状态为待评价
    try:
        # 根据订单id/订单所属用户/订单状态为待评价状态
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        # 查询订单所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")
    # 校验查询结果
    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    # 3.2 保存评价信息
    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1,如果订单已评价,让房屋成交量加1
        house.order_count += 1
        # add_all可以一次提交多条数据db.session.add_all([order,house])
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 提交数据,如果发生异常,进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 3.3 缓存中存储的房屋信息,因为订单成交,导致缓存中的数据已经过期,所以,需要删除过期数据
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK")
