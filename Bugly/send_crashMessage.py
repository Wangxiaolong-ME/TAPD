import logging
import os
import sys
import time

parentPath = os.path.abspath("..")
sys.path.append(parentPath)
from Apollo.apollo_api import version_config_switch, get_online_top_version, stop_config
from Bugly.bugly_config import app_id, online_versions, online_top_version
from Bugly.bugly_config import get_apollo_bugly_threshold
from Bugly.bugly_config import bustype
from Bugly.bugly_config import log
from AttaAPI.atta import atta_api

import RobotMessage.robot_config
from RobotMessage.robot_message import robot_message

from bugly import issueid_and_except, local_get_version, sort_by_access
from bugly import get_summary_data
from bugly import round_time

sendmessage_crash = []
sendmessage_anr = []
sendmessage_error = []

log = log()


def conversion_bugtype(bugtype):
    if bugtype == "Crash":
        return 1
    if bugtype == "Anr":
        return 2
    if bugtype == "Error":
        return 3


def get_bugly_url(bugtype, issueID):
    if bugtype == "Crash":
        type = "crashes"
    if bugtype == "Anr":
        type = "blocks"
    if bugtype == "Error":
        type = "errors"
    bugly_url = (f"http://bugly.oa.com/v2/crash-reporting/{type}/{app_id}/{issueID}"
                 f"/report?pid=1&version=all&start=0&date=last_7_day")
    return bugly_url


def out_text(bugtype, version, pr, vl, crash_user, issue_name, bugly_url):
    num = 0
    # 阿波罗Bugly阈值
    threshold = get_apollo_bugly_threshold()
    crash = threshold[0]
    anr = threshold[1]
    error = threshold[2]
    # crash
    crash_pr = crash['Probability']
    crash_vl = crash['Volatility']
    crash_u = crash['User']
    # anr
    anr_pr = anr['Probability']
    anr_vl = anr['Volatility']
    anr_u = anr['User']
    # error
    error_pr = error['Probability']
    error_vl = error['Volatility']
    error_u = error['User']
    if bugtype == "Crash":
        if pr > crash_pr and vl > crash_vl and crash_user > crash_u:
            logging.info(f"Crash阈值条件满足")
            num = 1
    if bugtype == "Anr":
        if pr > anr_pr and vl > anr_vl and crash_user > anr_u:
            logging.info(f"Anr阈值条件满足")
            num = 1
    if bugtype == "Error":
        if pr > error_pr and vl > error_vl and crash_user > error_u:
            logging.info(f"Error阈值条件满足")
            num = 1
    if num == 1:
        return f"版本号:{version}\n{bugtype}率为: {round(pr * 100, 3)}%,波动率为: {round(vl * 100, 3)}%,影响用户数为:{crash_user}\nTop Issues:\n{issue_name}|{bugly_url}"


def send_message():
    # 静态,动态配置版本方式 可切换
    online_switch = version_config_switch("online")
    version_list = local_get_version()  # [[纯版本],[版本号,活跃设备数]]

    if not version_list:
        # 重试获取
        time.sleep(10)
        version_list = local_get_version()
        if not version_list:
            sys.exit(1)     # 异常退出

    versions = sort_by_access(version_list[1], all_version=False)  # 按照活跃设备数排序
    top_version = get_online_top_version()  # 获取top_version

    if not online_switch:
        versions = online_versions  # 静态配置方式
    if not top_version:
        top_version = online_top_version    # 获取默认配置,前5个

    for type in bustype:
        for v in range(top_version):
            version = versions[v]   # 当前版本号
            logging.info("\n\n")
            logging.info(f"当前版本:{version}, 当前类型:{type}")
            # 1:Crash  2:Anr  3:Error
            bugtype = conversion_bugtype(type)
            data = get_summary_data(bugtype, version)
            if data is None:
                logging.error(f"data is None,版本:{version},{type}")
                continue
            # crash率
            pr = data[0]
            # 波动率
            vl = data[1]
            # 崩溃设备数量
            crash_user = data[2]

            # 上报埋点信息
            params = {
                "f1": version, "f2": type, "f3": pr, "f4": vl, "f5": crash_user
            }
            atta_id = "online_bugly_monitor"  # 线上bugly监控id
            try:
                atta_api(params, atta_id)
            except Exception as E:
                logging.warning(f"埋点上报接口请求失败!{E}")
                continue

            # issue ID和Name
            issue = issueid_and_except(bugtype, version)
            if not issue:
                logging.error(f"issue is None,版本:{version}, {type}, {issue}")
                continue
            issue_id = issue[0]
            issue_name = issue[1]
            # bugly链接
            bugly_url = get_bugly_url(type, issue_id)

            def build_message():
                mess = out_text(type, version, pr, vl, crash_user, issue_name, bugly_url)
                if not mess:
                    return None
                return mess

            if bugtype == 1:
                crash_message = build_message()
                if not crash_message:
                    continue
                sendmessage_crash.append(crash_message)
            if bugtype == 2:
                anr_message = build_message()
                if not anr_message:
                    continue
                sendmessage_anr.append(anr_message)
            if bugtype == 3:
                error_message = build_message()
                if not error_message:
                    continue
                sendmessage_error.append(error_message)


if __name__ == '__main__':
    # 是否执行程序
    stop = stop_config("online")
    if stop:
        logging.info("阿波罗配置程序停止,程序正常中止!")
        sys.exit()

    # 获取数据
    send_message()

    now = round_time()

    logging.info(sendmessage_crash)
    logging.info(sendmessage_anr)
    logging.info(sendmessage_error)

    if len(sendmessage_crash) >= 1:
        message = '\n\n'.join(sendmessage_crash)
        robot_message(f"时间段:{now}\nCrash: ❗ ❗ ❗ ❗\n\n{message}", RobotMessage.robot_config.key_bugly)

    if len(sendmessage_anr) >= 1:
        message = '\n\n'.join(sendmessage_anr)
        robot_message(f"时间段:{now}\nAnr: ❗ ❗\n\n{message}", RobotMessage.robot_config.key_bugly)

    if len(sendmessage_error) >= 1:
        message = '\n\n'.join(sendmessage_error)
        robot_message(f"时间段:{now}\nError:\n\n{message}", RobotMessage.robot_config.key_bugly)
