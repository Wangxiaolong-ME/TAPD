import base64
import datetime
import hmac
import json
import logging
import random
import time
import urllib.parse
import uuid
from hashlib import sha256
from operator import itemgetter

import jsonpath
import requests
from Bugly.bugly_config import sign_method
from Bugly.bugly_config import api_version
from Bugly.bugly_config import app_id
from Bugly.bugly_config import app_key
from Bugly.bugly_config import bugly_url


# 加密
def hash_256(message, secret):
    secret = secret.encode('utf-8')
    message = message.encode('utf-8')
    sha = hmac.new(secret, message, digestmod=sha256).hexdigest()
    sign = base64.b64encode(str.encode(sha))
    sign = str(sign, 'utf-8')
    url_str = urllib.parse.quote(sign)
    return url_str


# 生成加密签名串
def get_authorization(appid, appkey, body):
    nonce = random.randint(100000, 9999999)
    timestamp = int(time.time())
    hash_payload = hash_256(body, appkey)
    sign = f"appID={appid}&hashedPayload={hash_payload}&nonce={nonce}" \
           f"&signMethod={sign_method}&timestamp={timestamp}&version={api_version}"
    signature = hash_256(sign, appkey)
    auth = f"{sign}&signature={signature}"
    return auth


# BuglyAPI调用入口
def bugly_api(path, params):
    authorization = get_authorization(app_id, app_key, json.dumps(params))
    header = {
        "Authorization": authorization,
        "content-type": "application/json"
    }
    res = requests.post(f"{bugly_url}{path}", data=json.dumps(params), headers=header)
    # logging.info(f"请求实体:{res.request.body}")
    # logging.info((f"响应状态码:{res.status_code},响应内容:{res.json()}"))
    return res.json()


# API:获取5分钟间隔实时增量统计数据
def increment5(bugs, version="-1", date=None, start_end=None):
    """

    Args:
        bugs: 类型: 1：crash 2：anr   3:error
        version:版本
        date:期望获取的时间段
        start_end:开始结束时间段,列表

    Returns:res

    """
    url = '/stat/five_minutely/increment'
    if date is None and start_end is None:
        date = round_time()
        list = {"startDate": f"{date}", "endDate": f"{date}"}
    elif start_end is not None:
        start = round_time(start_end[0])
        end = round_time(start_end[1])
        list = {"startDate": f"{start}", "endDate": f"{end}"}
    else:
        list = {"startDate": f"{date}", "endDate": f"{date}"}
    # elif date is not None:
    #     date = round_time(date)
    #     list = {"startDate": f"{date}", "endDate": f"{date}"}
    # else:
    #     start = round_time(start_end[0])
    #     end = round_time(start_end[1])
    #     list = {"startDate": f"{start}", "endDate": f"{end}"}
    params = {
        "appID": app_id,
        "appPlatform": 1,
        **list,
        "appVersion": version,
        "busType": bugs,
        "requestID": str(uuid.uuid4())
    }
    res = bugly_api(url, params)
    return res


# API:获取5分钟间隔实时累计统计数据
def append5(bugs, version="-1", date=None, start_end=None):
    """

    Args:
        bugs: 类型: 1：crash 2：anr   3:error
        version:版本
        date:期望获取的时间段
        start_end:开始结束时间段,列表

    Returns:res

    """
    url = '/stat/five_minutely/append'
    if date is None and start_end is None:
        date = round_time()
        list = {"startDate": f"{date}", "endDate": f"{date}"}
    elif start_end is not None:
        start = round_time(start_end[0])
        end = round_time(start_end[1])
        list = {"startDate": f"{start}", "endDate": f"{end}"}
    else:
        list = {"startDate": f"{date}", "endDate": f"{date}"}
    # elif date is not None:
    #     date = round_time(date)
    #     list = {"startDate": f"{date}", "endDate": f"{date}"}
    # else:
    #     start = round_time(start_end[0])
    #     end = round_time(start_end[1])
    #     list = {"startDate": f"{start}", "endDate": f"{end}"}
    params = {
        "appID": app_id,
        "appPlatform": 1,
        **list,
        "appVersion": version,
        "busType": bugs,
        "requestID": str(uuid.uuid4())
    }
    res = bugly_api(url, params)
    return res


# API:获取5分钟增量issue top数据
def increment5_issue(bugs, version='-1', date=None):
    """

    Args:
        bugs: 类型: 1：crash 2：anr   3:error
        version:版本
        date:期望获取的时间段

    Returns:res

    """
    url = '/stat/five_minutely/issue/top'
    if date is None:
        date = round_time()
    # else:
    #     date = round_time(date)
    params = {
        "appID": app_id,
        "appPlatform": 1,
        "date": f"{date}",
        "appVersion": version,
        "busType": bugs,
        "requestID": str(uuid.uuid4()),
        "limit": 20
    }
    res = bugly_api(url, params)
    return res


# API:获取实时汇总信息
def summary(version='-1', date=None):
    """

    Args:
        version: 指定版本
        date: 默认取当前时间前一天的汇总数据,可输入要指定查询的日期

    Returns:

    """
    url = "/stat/realtime/summary"
    if date is None:
        today_start = datetime.datetime.now().replace(microsecond=0, hour=0, minute=0, second=0)
        today_end = datetime.datetime.now().replace(microsecond=0, hour=23, minute=0, second=0)
        day = datetime.timedelta(days=1)
        yesterday_start = today_start - day  # 00:00:00
        yesterday_end = today_end - day  # 23:00:00
        print(yesterday_start, yesterday_end)
    else:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        yesterday_start = date.replace(microsecond=0, hour=0, minute=0, second=0)
        yesterday_end = date.replace(microsecond=0, hour=23, minute=0, second=0)
        print(yesterday_start, yesterday_end)
    params = {
        "appID": app_id,
        "appPlatform": 1,
        "startHour": f"{yesterday_start}",
        "endHour": f"{yesterday_end}",
        "version": version,
        "requestID": str(uuid.uuid4())
    }
    res = bugly_api(url, params)
    return res


# 按天获取统计详情
def daily(bugs, date=None):
    url = '/stat/daily/detail'
    if date is None:
        # 默认为前两天(凌晨0点-2点左右前一天的数据还没有同步出来,会获取不到)
        date = (datetime.date.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    params = {
        "appID": app_id,
        "appPlatform": 1,
        "date": f"{date}",
        "busType": bugs,
        "requestID": str(uuid.uuid4()),
    }
    res = bugly_api(url, params)
    return res


# 按天获取crash率趋势
def daily_crash(bugs, version, date=None):
    url = '/stat/daily/trend'
    if date is None:
        # 默认为前一天
        date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        "appID": app_id,
        "appPlatform": 1,
        "appVersion": version,
        "startDate": f"{date}",
        "endDate": f"{date}",
        "busType": bugs,
        "requestID": str(uuid.uuid4()),
    }
    res = bugly_api(url, params)
    return res


# ----------------------tools-------------------------
# 将时间处理为5的倍数,规则:四舍五入,再向前取5分钟
def round_time(date=None, five_minute_handle=True):
    """
    five_minute_handle: 是否需要使用减5分钟的处理
    """
    if date is None:
        now = datetime.datetime.now().replace(microsecond=0)
        if five_minute_handle is True:
            five = datetime.timedelta(minutes=5)
            now = now - five
        minute_now = now.minute
        if minute_now % 10 < 5:
            m1 = minute_now % 10
        else:
            m1 = minute_now % 10 - 5
        new_time = now.replace(minute=minute_now - m1, second=0)
        # 如果输入时间是00:00-00:04:59之间,则时间会转为00:00:00,在此基础上时间将会进一步转为
        # 前一天的23:59:00
        # if newTime.hour == 0 and newTime.minute == 0:
        #     day = datetime.timedelta(days=1)
        #     newTime = newTime - day
        #     newTime = newTime.replace(hour=23, minute=59)
        #     return newTime
        return new_time
    else:
        if type(date) is not str:
            return date
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        if five_minute_handle is True:
            five = datetime.timedelta(minutes=5)
            date = date - five
        minute_now = date.minute
        minute = str(date).split(" ")[1].split(":")[1]
        if int(minute) % 10 < 5:
            m1 = int(minute) % 10
        else:
            m1 = int(minute) % 10 - 5
        new_time = date.replace(minute=minute_now - m1, second=0)
        # 如果输入时间是00:00-00:04:59之间,则时间会转为00:00:00,在此基础上时间将会进一步转为
        # 前一天的23:59:00
        # if newTime.hour == 0 and newTime.minute == 0:
        #     day = datetime.timedelta(days=1)
        #     newTime = newTime - day
        #     newTime = newTime.replace(hour=23, minute=59)
        #     return newTime
        return new_time


# 取历史7天时间段
def get_history(date=None, days=7, add_five_minute=False):
    """
    add_five_minute: 是否将历史时间加5分钟,应对接口请求时还会将时间减5,所以这里加5做个抵消
    """
    if date is None:
        now = round_time()
        day = datetime.timedelta(days=1)
        history = []
        for i in range(1, 8):
            if add_five_minute is False:
                his = now - day * i
                history.append(str(his))
            else:
                five = datetime.timedelta(minutes=5)
                his = (now + five) - day * i
                history.append(str(his))
        return history
    else:
        date = round_time(date)
        day = datetime.timedelta(days=1)
        history = []
        for i in range(1, days + 1):
            if add_five_minute is False:
                his = date - day * i
                history.append(str(his))
            else:
                five = datetime.timedelta(minutes=5)
                his = (date + five) - day * i
                history.append(str(his))
        return history


# 列表排序(冒泡),去除最大最小值
def list_sort(list):
    for i in range(len(list)):
        for j in range(len(list) - 1):
            if list[j] > list[j + 1]:
                a = list[j]
                list[j] = list[j + 1]
                list[j + 1] = a
    list.remove(list[0]), list.remove(list[-1])
    return list


# 取列表重复最多次的元素
def get_most_one(list):
    most_key = max(list, key=list.count)
    return most_key


# ----------------------tools-------------------------

def local_get_version():
    """
    return: [[版本号],[版本号,活跃设备数]]
    """
    res = daily(1)
    data = jsonpath.jsonpath(res, "$.data[*]")
    if not data:
        logging.warning(f"版本获取失败:{res}")
        return False
    versions = []
    versions_access = []
    for d in data:
        versions_access.append([d['appVersion'], int(d['accessUser1'])])
        versions.append(d['appVersion'])
    return [versions, versions_access]


# 汇总数据 1.crash率 2.波动率 3.crash设备数量
def get_summary_data(bugs, version='-1'):
    logging.info(f"get_summary_data,请求时间段:{round_time()}")
    res = increment5(bugs, version)
    data = jsonpath.jsonpath(res, "$.data[0]")
    try:
        if data is False or str(data) == 'None':
            logging.error(f"data为空,res:{res}")
            return None
        # 崩溃设备数,联网设备数
        crash_user = jsonpath.jsonpath(res, "$.data[0].crashUser")[0]
        access_user = jsonpath.jsonpath(res, "$.data[0].accessUser")[0]
        if int(crash_user) == 0:
            logging.error(f"设备数为0,res:{res}")
            return None
        # crash率
        pr = round((int(crash_user) / int(access_user)), 5)
        logging.info(f"crashUser:{crash_user},accessUser:{access_user}")

        crash_user_history = []
        history = get_history()
        logging.info(f"历史时间段:{history}")
        for i in range(len(history)):
            r = increment5(bugs, version, history[i])
            users = jsonpath.jsonpath(r, "$.data[0].crashUser")[0]
            crash_user_history.append(int(users))
        # 对crashUser列表进行去除最大和最小值
        list = list_sort(crash_user_history)
        # 历史crash设备平均值
        crash_avg = round(sum(list) / len(list), 2)
        if crash_avg == 0:
            logging.error(f"历史平均值为0,历史设备数:{crash_user_history}")
            return None
        # 波动率 (崩溃数 - 历史平均崩溃数) / 历史平均崩溃数
        vl = round((int(crash_user) - float(crash_avg)) / float(crash_avg), 5)
        logging.info(f"历史crash设备{list},平均值:{crash_avg},crash率:{pr},波动率:{vl}")

    except Exception as e:
        logging.error(f"获取数据出错,信息:{e}")
        return None

    return pr, vl, int(crash_user)


# Issue ID和崩溃名称
def issueid_and_except(bugs, version='-1'):
    logging.info(f"issueid_and_except,请求时间段:{round_time()}")
    res = increment5_issue(bugs, version)
    data = jsonpath.jsonpath(res, "$.data.detail[*]")
    if data is False or str(data) == 'None':
        logging.error(f"{data},{res}")
        return None
    # ID和Name
    issue_id = jsonpath.jsonpath(res, "$.data.detail[*].issueID")
    issue_name = jsonpath.jsonpath(res, "$.data.detail[*].exceptionName")
    # 取重复最多的exceptionName
    most_issue_name = get_most_one(issue_name)
    # 对应重复最多exceptionName的issueID
    most_issue_id = issue_id[issue_name.index(most_issue_name)]
    return most_issue_id, most_issue_name


def sort_by_versions(version_data):

    def sort_demo(split_list):
        version_list = sorted(split_list, key=itemgetter(0, 1, 2, 3), reverse=True)
        index_list = []
        for index in version_list:
            index_list.append(index[-1])
        return index_list

    versions = version_data  # 纯版本号列表
    all_version_access = versions[0]  # 全本版提前捞出来,最后插入到第一位

    # 先删除-1全版本
    versions.pop(0)

    # 切分版本号
    split_version = []
    for ver in versions:
        split_ver = ver.split('.')
        if len(split_ver) == 4:
            one, two, three, four = int(split_ver[0]), int(split_ver[1]), int(split_ver[2]), int(split_ver[3])
        elif len(split_ver) == 3:
            one, two, three, four = int(split_ver[0]), int(split_ver[1]), int(split_ver[2]), None
        else:
            logging.warning(f"未能切分版本号: {ver}")
            continue
        split_version.append([one, two, three, four, versions.index(ver)])

    # 按版本从大到小排序,返回索引
    index_list = sort_demo(split_version)
    sort_list = []
    for index in index_list:
        sort_list.append(versions[index])

    # 把全版本数据插入第一位
    sort_list.insert(0, all_version_access)

    return sort_list


def sort_by_access(version_access, only_version=True, all_version=True):
    """
    all_version: 返回版本列表中加入-1全版本
    only_version: True,只返回版本号;False,返回版本号和活跃设备数
    """
    if '-1' in version_access[0]:
        all_version_access = version_access[0]  # 全本版提前捞出来,最后插入到第一位
        version_access.pop(0)
    else:
        all_version_access = None

    # 按活跃设备数从大到小排序
    final_list = sorted(version_access, key=itemgetter(1), reverse=True)

    # 只提取版本号
    version_list = []
    for version in final_list:
        version_list.append(version[0])

    if all_version:
        # 把全版本数据插入第一位
        if all_version_access:
            final_list.insert(0, all_version_access)
        version_list.insert(0, '-1')

    if only_version:
        return version_list
    return final_list


# bugly日报
def daily_bugly(bugs, version='-1'):
    """
    return: [崩溃次数,崩溃设备数,联网设备数]
    """
    res = daily_crash(bugs, version)
    data = jsonpath.jsonpath(res, "$.data[0]")
    try:
        if data is False or str(data) == 'None':
            logging.error(f"data为空,res:{res}")
            return None
        # 奔溃次数,崩溃设备数,联网设备数
        crash_num = jsonpath.jsonpath(res, "$.data[0].crashNum")[0]
        crash_user = jsonpath.jsonpath(res, "$.data[0].crashUser")[0]
        access_user = jsonpath.jsonpath(res, "$.data[0].accessUser")[0]

        return [int(crash_num), int(crash_user), int(access_user)]

    except Exception as e:
        logging.error(f"获取数据出错,信息:{e}")
        return None
