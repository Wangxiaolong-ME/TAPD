import logging
import sys

from Apollo.apollo_api import AutoForwardConfig
from Tapd.Module.tapd_module import TapdModule
from RobotMessage.robot_config import key_forward_requirements
from RobotMessage.robot_message import robot_message

sys.path.append('..')


def forward_module(entity):
    logging.info(" ========== forward_module running .... ========== ")
    message = []

    # 流转模块初始化,生成配置文件
    init_forward = AutoForwardConfig.AutoForwardFTConfig()
    init_forward.build_config()

    owner_list = entity.keys()
    point = {}  # 埋点
    for current_owner in owner_list:
        logging.info(f"当前处理人: {current_owner}")

        if not entity[current_owner]:
            logging.warning(f"当前处理人:{current_owner}用反数量 0")
            continue

        entry_id_list = entity[current_owner].keys()

        if entry_id_list:
            for entry_id in entry_id_list:
                data = entity[current_owner][entry_id]

                logging.info(f"Forward_module Start bug_id: {data.bug_id}")

                forward = TapdModule.AutoForwardModule(data, init_forward)  # 自动流转模块

                # 根据标题分词自动流转转需求,目前仅适用安卓平台
                if "Android" == data.platform:
                    try:
                        forward_message, keywords = forward.main()  # 流转
                        if forward_message:

                            # 自动流转埋点
                            forward_result = True

                            # 关键词埋点
                            if len(keywords) == 1:
                                keyword = keywords[0]
                                second_keyword = None
                            else:
                                keyword = keywords[0]
                                second_keyword = keywords[1]

                            message.append(forward_message)

                            point[entry_id] = {
                                "bug_id": data.bug_id,
                                "title": data.title,
                                "url": data.url,
                                "first_class": data.first_class,
                                "platform": data.platform,
                                "version": data.version[0],
                                "phone_model": data.phone_model,
                                "forward": forward_result,
                                "keyword": keyword,
                                "second_keyword": second_keyword
                            }

                        else:
                            logging.warning(keywords)

                    except Exception as E:
                        logging.warning(f"Forward_module exception!,{E}")
                        continue
                else:
                    logging.info("platform isn't Android, continue...")

    # 输出日志内容:此次过程流转了多少条用反
    forward_num = len(point.keys())
    logging.info(f"Forward_module:deal with {forward_num} tapd in this process")
    if len(message) > 0:
        message = '\n\n'.join(message)
        robot_message(message, key_forward_requirements)  # 发送群消息-->产品小群
    return point
