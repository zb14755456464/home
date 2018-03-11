
# coding=utf-8

import logging
from CCPRestSDK import REST
import ConfigParser

# 帐号
accountSid= '8aaf07085f9eb021015fb58c56d906e8'

# 主帐号Token
accountToken= 'e21ca96da61c49ee97e0fdf1ba47de5a'

# 应用Id
appId='8aaf07085f9eb021015fb58c574106ef'

# 请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

# 请求端口
serverPort='8883'

# REST版本号
softVersion='2013-12-26'

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id


# 希望用单例实现
# 使用一个属性来记录初始化的代码内容. 之后如果发现已经有属性的值了, 就直接返回即可

class CCP(object):

    def __new__(cls):
        # 判断系统是否有instance的值
        if not hasattr(cls, 'instance'):
            # 创建instance
            # cls.instance = super(CCP, cls).__new__(cls)
            # # 实现一些需要初始化的代码
            # # 初始化REST SDK
            # cls.instance.rest = REST(serverIP, serverPort, softVersion)
            # cls.instance.rest.setAccount(accountSid, accountToken)
            # cls.instance.rest.setAppId(appId)
            obj = super(CCP, cls).__new__(cls)
            # 实现一些需要初始化的代码
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        # 如果是第二次进来, 直接返回即可
        return cls.instance

    def send_template_sms(self, to,datas,temp_id):

        # 1. 调用发短信接口
        try:
            result = self.rest.sendTemplateSMS(to, datas, temp_id)
        except Exception as e:
            logging.error(e)
            raise e

        # 通过打印查看, 我们发现如果返回statusCode为6个0,就表示发送成功
        #{'templateSMS': {'smsMessageSid': 'cfb833c890b3480cb84457077a0e545e', 'dateCreated': '20171201100239'},
        # 'statusCode': '000000'}
        # smsMessageSid:cfb833c890b3480cb84457077a0e545e
        # dateCreated:20171201100239
        # statusCode:000000
        print result

        # 2. 获取statusCode, 判断是否发送成功
        status_Code = result.get('statusCode')

        if status_Code == '000000':
            return 0
            # 3. 需要告诉服务器是否成功. 我们这里暂时定义, 返回0就是成功, 返回-1就是失败
        else:
            return -1


# ccp = CCP() # 希望帮我们把鉴权的代码封装起来, 只调用一次
# # 使用时, 直接调用方法传参即可
# ccp.send_template_sms('17610812003', ["1234", 5], 1)

    
   
#sendTemplateSMS(手机号码,内容数据,模板Id)

if __name__ == '__main__':
    ccp = CCP()
    result =  ccp.send_template_sms('17610812003', ["1234", 5], 1)