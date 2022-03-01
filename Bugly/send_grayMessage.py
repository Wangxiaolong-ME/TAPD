# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import sys
import os

parPath = os.path.abspath("..")
sys.path.append(parPath)
# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------

import logging
from collections import defaultdict
from Apollo.apollo_api import stop_config
from RobotMessage.robot_message import robot_message
from RobotMessage.robot_config import key_grayBugly
from Bugly.gray_crash import start_end, get_gray_version
from Bugly.gray_crash import get_summary_data
from Bugly.bugly_config import app_id
from Bugly.bugly_config import log
from Bugly.bugly_config import bustype
from AttaAPI.atta import atta_api
import jsonpath

log = log()


# 清洗数据:
# 对每个版本下.每个bug类型下.所有时间段下.
# 1.不同issueName下相同的issueID去重,并打印重复的次数;
# 2.崩溃设备和活跃设备求和
# 返回最终字典数据
def get_wash_summary(summary_info):
    final_dict = {}
    version = list(summary_info.keys())
    for v in version:
        # 版本号下 所有信息
        version_info = summary_info.get(v)
        summary_dict = main(version_info, v)
        final_dict[v] = summary_dict
    return final_dict


def main(version_info, version):
    different_bugtype_summary = {"Crash": "", "Anr": "", "Error": ""}
    for type in bustype:
        # 当前bug类型下时间段列表集合
        date = jsonpath.jsonpath(version_info, f"$.{type}..date")
        if date is not False:
            # 获取issueINFO
            issueinfo = get_issueinfo(date, version_info, type)
            crash_sum, access_sum = get_users(date, version_info, type)
            # 去除重复issueINFO
            new_issueinfo = wash_issueinfo(issueinfo, version, type)
            different_bugtype_summary[type] = {"issueInfo": new_issueinfo, "crashUser": crash_sum,
                                               "accessUser": access_sum}
    return different_bugtype_summary


# 将所有时间段的issueInfo合并
def get_issueinfo(date, version_info, type):
    issueinfo = defaultdict(list)
    for d in date:
        # 每个issueInfo中的 每组列表数据 长度为2，第一个元素是字符串，是issueName，第二个元素是列表，里面有一个至多个issueID
        issuetxt = jsonpath.jsonpath(version_info, f"$.{type}..{d}.issueInfo[*]")
        # 取 每组数据列表 中的第一个元素，即issueName
        for n in range(len(issuetxt)):
            issue_name = issuetxt[n][0]
            issue_id = issuetxt[n][1]
            issueinfo[issue_name].append(issue_id)
    issueinfo = dict(issueinfo)
    return issueinfo


# 获取崩溃设备数和活跃设备数
def get_users(date, version_info, type):
    crash_sum = 0
    access_sum = 0
    for d in date:
        crash_user = jsonpath.jsonpath(version_info, f"$.{type}..{d}.crashUser")[0]
        access_user = jsonpath.jsonpath(version_info, f"$.{type}..{d}.accessUser")[0]
        crash_sum = crash_sum + crash_user
        access_sum = access_sum + access_user
    return crash_sum, access_sum


# 将issueName去重
def wash_issueinfo(issueinfo, version, bugtype):
    # 通过获取issueinfo的键得到issueName列表
    issue_name = list(issueinfo.keys())
    # 新issueInfo字典容器(用来存放issueID去重后，issueName：issueID)
    new_issue = {}
    for name in issue_name:
        issue_id = issueinfo.get(name)
        # 创建用来接收 去重后的issueID 字典
        issueid_dic = defaultdict(list)
        for id in issue_id:
            id = ''.join(id)  # 去中括号
            issueid_dic[id].append(id)
        # 取issueID字典的键，完成去重，值的长度就是重复的次数
        wash_id = list(issueid_dic.keys())
        for num in wash_id:
            if len(issueid_dic[num]) > 2:
                logging.info(f"版本：{version} ，{bugtype}：issueID：{num} 出现{len(issueid_dic[num])}次")
        new_issue[name] = wash_id
    return new_issue


# 将版本号下的数据进行清洗,version:issue,user
def get_version_summary(wash_summary):
    # 所有版本号
    versions = list(wash_summary.keys())
    summary_info = {}
    for version in versions:
        # 版本号下的数据
        version_info = wash_summary.get(version)
        issue, user = get_issue_and_user(version_info)
        summary_info[version] = {"issue": issue, "user": user}
    return summary_info


# 埋点数据上报ATTA,数据取get_version_summary返回的数据
def output_atta(summary_info):
    # 所有版本号
    versions = list(summary_info.keys())

    for version in versions:
        # 获取当前版本下的数据
        info = summary_info.get(version)

        # Bug类型:"Crash", "Anr", "Error"
        bugtype = ["Crash", "Anr", "Error"]

        for tp in bugtype:
            # issue字典 {Name:ID列表},目的:拿到所有Name的ID列表长度,既:issueID总数
            bugtype_issue = info["issue"].get(tp)
            if bugtype_issue is not False:
                # 所有issueName: 'SIGSEGV(SEGV_MAPERR)','SIGILL(ILL_ILLOPC)'
                issue_name = list(bugtype_issue.keys())

                issue_sum = 0
                # 所有issueName的ID列表长度:
                for num in issue_name:  # num:issueName
                    # issueID总数 赋值
                    issue_num = len(bugtype_issue[num])  # bugtype_issue[num]:issueName下的ID列表,拿ID列表长度
                    issue_sum = issue_sum + issue_num
            else:
                logging.warning(f"版本:{version},没有{tp}类型Issue信息")
                issue_sum = 0

            # user字典 {crashUser:12,accessUser:6731}
            bugtype_user = info["user"].get(tp)
            # 崩溃设备 赋值
            crash_num = bugtype_user["crashUser"]
            if crash_num is False:
                crash_num = 0
            # 活跃设备 赋值
            access_num = bugtype_user["accessUser"]
            if access_num is False:
                access_num = 0

            # 上报埋点
            params = {
                "f1": version, "f2": tp, "f3": crash_num, "f4": access_num,
                "f5": issue_sum
            }
            atta_api(params, "graryscale_buglymonitor")


# 获取版本下的issue数据和相关设备数数据
def get_issue_and_user(version_info):
    # 版本号下各类型 issue信息
    bugtype_issueinfo = {"Crash": "", "Anr": "", "Error": ""}
    # 版本号下各类型 user信息
    bugtype_users = {"Crash": "", "Anr": "", "Error": ""}
    for type in bustype:
        issueinfo = jsonpath.jsonpath(version_info, f"$.{type}.issueInfo")
        crash_user = jsonpath.jsonpath(version_info, f"$.{type}.crashUser")
        access_user = jsonpath.jsonpath(version_info, f"$.{type}.accessUser")
        if issueinfo is not False:
            bugtype_issueinfo[type] = issueinfo[0]
        else:
            bugtype_issueinfo[type] = False
        if crash_user and access_user is not False:
            bugtype_users[type] = {"crashUser": crash_user[0], "accessUser": access_user[0]}
        else:
            bugtype_users[type] = {"crashUser": False, "accessUser": False}
    return bugtype_issueinfo, bugtype_users


# 加工重组获取URL
def get_url(bugtype, issueID):
    if bugtype == "Crash":
        type = "crashes"
    if bugtype == "Anr":
        type = "blocks"
    if bugtype == "Error":
        type = "errors"
    bugly_url = (f"http://bugly.oa.com/v2/crash-reporting/{type}/{app_id}/{issueID}"
                 f"/report?pid=1&version=all&start=0&date=last_7_day")
    return bugly_url


# 不同bug类型的告警级别
def different_level(bugtype):
    type = ["Crash", "Anr", "Error"]
    if bugtype == type[0]:
        return " ❗ ❗ ❗ ❗"
    if bugtype == type[1]:
        return " ❗ ❗"
    if bugtype == type[2]:
        return ""


# 输出可发送的message消息
def output_message(version_summary, webhook=None):
    """

    :param version_summary: 处理后包含版本的数据
    :param webhook: 机器人key
    :return:
    """
    starttime, endtime = start_end()
    version = version_summary.keys()
    summary_message = []  # 包含各版本的集合信息
    for v in version:
        # 当前版本下所有类型的数据集合
        current_version_summary_message = []
        # 当前版本下的数据集合
        summary = version_summary.get(v)
        # issue数据集合
        issueinfo = summary.get("issue")
        # user数据集合
        user = summary.get("user")
        for type in bustype:
            type_message = []  # 包含当前类型的集合信息
            # 当前bug类型下的issue信息(issueName:issueID)
            issue_summary = issueinfo.get(type)
            # 当前bug类型下的user信息(crashUser,accessUser)
            user_summary = user.get(type)
            if issue_summary is not False and user_summary is not False:
                crash_user = user_summary.get("crashUser")
                access_user = user_summary.get("accessUser")
                issue_name_list = list(issue_summary.keys())  # issueName列表
                issue_message = []  # 当前类型下的issue信息(所有的issueName对应issueID)
                for name in issue_name_list:
                    issue_id_list = issue_summary.get(name)  # 当前issueName对应的所有issueID列表
                    issue_url_list = []  # 当前issueName下的issueUrl列表
                    for id in issue_id_list:
                        issue_url = get_url(type, id)
                        issue_url_list.append(f"{issue_url}")
                    issue_url_list = '\n\n'.join(issue_url_list)
                    message = f"ExceptionName: {name}:\nIssueURL:\n{issue_url_list}"
                    issue_message.append(message)
                issue_message = '\n\n'.join(issue_message)
                level_tag = different_level(type)  # 根据bug类型划分报警级别,Crash:4个叹号,Anr:2个叹号,Error:正常
                type_message.append(f"{type}:{level_tag}\n影响设备: {crash_user},活跃设备: {access_user}\n{issue_message}")
            else:
                logging.warning(f"版本:{v},类型{type},没有issue或影响设备信息")
                continue
            type_message = '\n\n'.join(type_message)

            # 由于全部内容过大，群消息接口不支持，所以拆分为每个bug类型发送
            robot_message(f"时间范围：{starttime} - {endtime}\n版本: {v}\n\n{type_message}", webhook)

            # 将当前类型的数据追加到当前版本的总数据集合下
            current_version_summary_message.append(type_message)
        if len(current_version_summary_message) < 1:
            logging.warning(f"当前版本{v}没有issue相关信息")
            continue
        summary_str = '\n'.join(current_version_summary_message)
        # 这里返回当前版本下所有数据集合
        summary_message.append(f"时间范围：{starttime} - {endtime}\n版本: {v}\n\n{summary_str}")
    if len(summary_message) < 1:
        logging.warning(f"无任何issue信息")
        return None
    # 所有版本的数据集合
    return summary_message


if __name__ == '__main__':
    # 是否执行程序
    stop = stop_config("gray")
    if stop:
        logging.info("阿波罗配置程序停止,程序正常中止!")
        sys.exit()
    version = get_gray_version()
    # 1.获取时间段下灰度版本所有内容
    data = get_summary_data(version)
    # 2.清洗数据,IssueID去重,crash和access User求和
    wash_data = get_wash_summary(data)
    # 3.将版本号下的数据进行清洗
    new_data = get_version_summary(wash_data)
    # 4.上报埋点
    output_atta(new_data)
    # 5.将数据进行最后提取,重组为要发送的message文案
    message = output_message(new_data, key_grayBugly)
    # 输出下日志
    logging.info(message)
