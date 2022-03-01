import logging
import time

import requests


def atta_api(params_dict, atta_id):
    """

    :param params_dict: 参数键值对
    :param atta_id: ATTA关联灯塔的事件code,一个事件对应一个ATTAID; 用反:user_feedback 灰度Bugly监控:grayscale_buglymonitor
    :return:

    """
    url = "http://h.trace.qq.com/kv"
    data = {
        "attaid": "XXXX",
        "token": "XXX",
        "AttaID": atta_id,
        **params_dict

    }
    response = requests.post(url=url, data=data)
    if not response:    # 接口请求失败,过10秒再重试一次
        logging.warning("atta_api request fail, try again!")
        time.sleep(10)
        response = requests.post(url=url, data=data)
    logging.info(f"埋点上报----状态码:{response.status_code}")
