# -*- coding: utf-8 -*-

from qiniu import Auth, put_file, etag, urlsafe_base64_encode, put_data
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = '6HpJXhnT1MS70c7GjT--UrvRn6sMsxwDkIQ1fYQq'
secret_key = 'rn0V8J7trKklJwTRA8arYoFFCOe6OftoCt_w-s-4'


def storage(file_data):
    """上传图片到七牛, file_data是文件的二进制数据"""
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'itheimaihome'

    # 我们不需要这个Key. 图片的上传是form表单提交.
    # key = 'my-python-logo.png';

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)
    # ret, info = put_file(token, key, localfile)
    # 我们这个是通过form表单提交的, 不需要用到put_file方法
    ret, info = put_data(token, None, file_data)

    # print(info)
    # print(ret)

    if info.status_code == 200:
        # 表示上传成功， 返回文件名
        # 我们上传成功之后, 需要在别的页面显示图像, 因此需要返回图像名
        return ret.get("key")
    else:
        # 表示上传失败
        raise Exception("上传失败")
    # http://ozcxm6oo6.bkt.clouddn.com/FnTUusE1lgSJoCccE2PtYIt0f7i3

if __name__ == '__main__':
    # 打开图片数据
    with open("./1.png", "rb") as f:
        # 读取图片数据二进制数据
        file_data = f.read()
        # 上传图片书记到七牛云
        result = storage(file_data)
        print result

        # result 就存储的是图片名. 将来就可以再程序中调用显示
















