# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import logging
import sys, os

parPath = os.path.abspath("..")
sys.path.append(parPath)

# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import json
import requests
from RobotMessage.robot_config import key_me


# 例如:robot_message("test","<@zhangsan><@lisi><@all>")
def robot_message(text, key=None, user=None, in_type="text"):
    """

    Args:
        text: 文本内容
        key: 发送目标群的机器人Webhook_key
        user: @群成员

    Returns:

    """
    # robot_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?debug=1"    # debug模式
    robot_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    if key is None:
        params = {"key": key_me}
    else:
        params = {"key": key}
    if user is None:
        data = {
            "msgtype": in_type,
            in_type: {
                "content": f"{text}"
            }
        }
    else:
        data = {
            "msgtype": in_type,
            in_type: {
                "content": f"{user}\n{text}"
            }
        }
    json_data = json.dumps(data)  # 序列化；字典--->文本，方便HTTP传输
    response = requests.post(url=robot_url, data=json_data, params=params)
    logging.info(f"请求头:{response.request.headers},响应码:{response.status_code},响应实体:{response.json()}")

