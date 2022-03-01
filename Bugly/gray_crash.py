# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import datetime
import json
import logging
import sys, os
import time
from operator import itemgetter

parPath = os.path.abspath("..")
sys.path.append(parPath)
from collections import defaultdict
import jsonpath
from Apollo.apollo_api import get_gray_threshold, version_config_switch
from Bugly.bugly_config import bustype, max_access_user, min_access_user, gray_versions

# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
from bugly import increment5, increment5_issue, round_time, local_get_version, sort_by_access, sort_by_versions


def get_gray_version():
    # 静态,动态配置版本方式 可切换
    gray_switch = version_config_switch("gray")
    if not gray_switch:
        versions = gray_versions    # 静态方式 获取阿波罗版本号
        return versions

    versions_data = local_get_version()
    if not versions_data:
        # 重试获取
        time.sleep(10)
        versions_data = local_get_version()
        if not versions_data:
            sys.exit(1)     # 异常退出

    all_versions = versions_data[0]
    version_access = versions_data[1]
    sort_versions = sort_by_versions(all_versions)
    sort_access_versions = sort_by_access(version_access, only_version=False)  # 按照活跃数排序
    sort_versions.pop(0)
    sort_access_versions.pop(0)
    max_access_version = sort_access_versions[0][0]  # 最大活跃数版本号
    max_index = sort_versions.index(max_access_version)  # 最大活跃数版本在所有版本列表中的索引

    sort_access_versions = dict(sort_access_versions)  # 转换字典,方便取值

    # 取大于最大活跃数的版本
    max_version = []
    for version in range(max_index):
        max_version.append(sort_versions[version])

    # 取版本的活跃设备数
    max_version_access = []
    for version in max_version:
        max_version_access.append([version, sort_access_versions[version]])

    # 取其中最大活跃数的版本
    sort_max_version_access = sorted(max_version_access, key=itemgetter(1), reverse=True)

    # 获取阿波罗灰度阈值配置
    gray_access_user = get_gray_threshold()
    if gray_access_user:
        max_acc = gray_access_user[0]
        min_acc = gray_access_user[1]
    else:  # 使用本地备用配置
        max_acc = max_access_user
        min_acc = min_access_user

    # 阈值条件判断
    if min_acc < sort_max_version_access[0][1] < max_acc:
        gray_version = sort_max_version_access[0][0]
        logging.info(f"灰度版本: {gray_version}, 活跃设备数: {sort_max_version_access[0][1]}")
    else:
        gray_version = None
        logging.info(f"灰度版本: None, 最大版本:活跃设备数: "
                     f"{sort_max_version_access[0][0]}: {sort_max_version_access[0][1]}")

    return gray_version


# 获取时间段列表
def get_start_date(res):
    """

    Args:
        res: 接口返回的json数据

    Returns:statDate时间段列表

    """
    try:
        # 清理出不为0的crash时间段数据
        data = jsonpath.jsonpath(res, "$.data[*]")
        statDate = []
        for i in range(len(data)):
            crashUser = int(jsonpath.jsonpath(data[i], "$.crashUser")[0])
            # print(crashUser)
            if crashUser != 0:
                stat = jsonpath.jsonpath(data[i], "$.statDate")[0]
                statDate.append(stat)
        return statDate
    except Exception as e:
        logging.warning(f"Exception:{e}")
        return False


# 获取所有时间段对应的issue信息,{date:[[id],[name]]}
def get_issue_info(bugtype, version, statDate):
    """

    :param bugtype:
    :param version:
    :param statDate: 时间段列表
    :return: issue_info字典:{date:[[id],[name]]}
    """
    issue_info = {}
    crashUser = {}
    accessUser = {}
    for date in statDate:
        res = increment5_issue(bugtype, version, date)
        try:
            issueID = jsonpath.jsonpath(res, "$.data.detail[*].issueID")
            issueName = jsonpath.jsonpath(res, "$.data.detail[*].exceptionName")
            if issueID is not False and issueName is not False:
                # 将所有issueID和NAME赋进字典
                issue_info[date] = [issueID, issueName]
                try:
                    # 获取当前时间段下崩溃设备和活跃设备，理论上issueID不为False 则当前时间段一定有崩溃数
                    r = increment5(bugtype, version, date)
                    data = jsonpath.jsonpath(r, "$.data[0]")
                    if data is not False:
                        crash = jsonpath.jsonpath(r, "$.data[0].crashUser")[0]
                        access = jsonpath.jsonpath(r, "$.data[0].accessUser")[0]
                        crashUser[date] = int(crash)
                        accessUser[date] = int(access)
                    else:
                        crashUser[date] = 0
                        accessUser[date] = 0
                except Exception as e:
                    logging.error(f"当前时段已获取到IssueID，但获取崩溃数失败，信息：{e}；系统已将崩溃数初始化为0")
                    crashUser[date] = 0
                    accessUser[date] = 0
            else:
                issue_info[date] = ['None']
        except Exception as e:
            print(res, "报错信息:%s" % e)
    try:
        # 剔除值为None的字典键值对和列表元素
        for d in statDate[::-1]:
            if len(issue_info['%s' % d]) == 1:
                del issue_info['%s' % d]
                statDate.remove(d)
    except Exception as e:
        print("报错信息:%s" % e)
    return wash_issue(statDate, issue_info, crashUser, accessUser)


# 剔除值为None的字典键值对和列表元素
def clear_issue_info(issue_info, stat_date):
    """

    Args:
        issue_info: issue_info字典信息
        stat_date : 时间段列表

    Returns:去除空值,重组后的issue_info和时间段列表

    """
    for d in stat_date[::-1]:
        if len(issue_info['%s' % d]) == 1:
            del issue_info['%s' % d]
            stat_date.remove(d)
    return issue_info, stat_date


# 通过exceptionName的索引获取对应issueID并对Name去重，将issueID聚合到相同的exceptionName下
def merge_exception_name(id_list, name_list, crash_user, access_user, date):
    """

    Args:
        :param date: 当前时间段
        :param id_list: issueID列表
        :param name_list: issueName列表
        :param access_user: 崩溃设备
        :param crash_user: 活跃设备

    Returns: new_dict, issueName 对应 issueID 键值对

    """
    dic = defaultdict(list)
    # 获取所有issueName的索引
    for index, key in enumerate(name_list):
        dic[key].append(index)
    new_dict = defaultdict(list)
    for keys in dic.keys():
        # 此处建一个存放issueID的列表，先将同一类型下所有ID放一起
        idlist = []
        for index in dic[keys]:
            idlist.append(id_list[index])
        # 将同一Issue异常类型的ID放进字典
        new_dict["issueInfo"].append([keys, idlist])
        new_dict["crashUser"] = crash_user
        new_dict["accessUser"] = access_user
        new_dict["date"] = date
    return dict(new_dict)


# 将聚合后的信息合并进原字典中
def wash_issue(date_list, issue_dict, crash_user, access_user):
    """

    :param date_list:
    :param issue_dict:
    :param crash_user:
    :param access_user:
    :return:
    """
    # 遍历所有时间段
    for d in date_list:
        # 遍历一个时间段里的id和name
        info = []
        for id_name in issue_dict[d]:
            # [ [issueID] , [issueName] ]
            info.append(id_name)
        # [0]:id,[1]:name
        currentDateCrashUser = crash_user[d]
        currentDateAccessUser = access_user[d]
        kw = merge_exception_name(info[0], info[1], currentDateCrashUser, currentDateAccessUser, d)
        issue_dict[d] = kw
    return issue_dict


def conversion_bugtype(bugtype):
    if bugtype == "Crash":
        return 1
    if bugtype == "Anr":
        return 2
    if bugtype == "Error":
        return 3


# 崩溃设备数量
def crash_access_users(bugs, version, date=None):
    res = increment5(bugs, version, date)
    data = jsonpath.jsonpath(res, "$.data[0]")
    if data is not False:
        crashUser = jsonpath.jsonpath(res, "$.data[0].crashUser")[0]
        accessUser = jsonpath.jsonpath(res, "$.data[0].accessUser")[0]
        return crashUser, accessUser
    else:
        return None


# ------------------tools-----------------------
def start_end(time_slor=4):
    """

    Args:
        time_slor: 时间范围,默认4小时

    Returns:

    """
    now = round_time(five_minute_handle=False)
    logging.info(f"请求时间:{now}")
    hour = datetime.timedelta(hours=1)
    start = now - hour * time_slor
    # 如果取时间范围起点,日期到前一天,那么最大只取到当天的0点
    if start.day < now.day:
        start_time = now.replace(hour=0, minute=0, second=0)
    else:
        start_time = start
    end_time = now
    logging.info(f"时间范围:{start_time} - {end_time}")
    return start_time, end_time


# ------------------tools-----------------------

def get_summary_data(versions):
    """

    :param versions: 列表形式的版本号
    :return:
    """
    # 加入流水线后,传入的versions如果只有一个会自动变成str类型
    if type(versions) is not list:
        version_list = []
        version_list.append(versions)
        versions = version_list

    summary = {}
    start_end_list = start_end()
    for version in versions:
        summary[version] = {"Crash": "", "Anr": "", "Error": ""}
        for btype in bustype:
            # 1:Crash  2:Anr  3:Error
            bugtype = conversion_bugtype(btype)

            # 如果res没有获取到,重试一次
            for retry in range(0, 2):
                # 获取时间段,crash设备数
                res = increment5(bugtype, version, start_end=start_end_list)
                if res is not False:
                    # 时间段列表
                    statDate = get_start_date(res)
                    break
                else:
                    time.sleep(10)
                    continue

            if statDate is not False:
                # issue信息,字典
                issueInfo = get_issue_info(bugtype, version, statDate)
                # 将issue信息作为值追加到字典的type键中
                summary[version][btype] = issueInfo
            else:
                logging.warning(f"type:{btype},get_start_date is False,continue")
                continue

    summary = dict(summary)
    return summary
