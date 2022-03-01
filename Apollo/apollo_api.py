import csv
import json
import logging
from collections import defaultdict

import jieba
import jsonpath
import pandas as pd
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from Apollo.apollo_config import apolloUrl
from Apollo.apollo_config import get_key
from Apollo.apollo_config import get_id
from Apollo.apollo_config import anrdefault
from Apollo.apollo_config import crashdefault
from Apollo.apollo_config import errordefault
from Apollo.apollo_config import version_backup


# 按key拉取
def apollo(config_key):
    """
    businessKey	String	''	否	业务key
    moduleKey	String	''	否	模块key
    configKey	String	''	否	配置key
    gray	    Gray	{}	否	灰度配置字段

    """
    url = f"{apolloUrl}{get_key}"
    data = {
        "businessKey": "AndroidBaseArch",
        "moduleKey": "auto_doraemon",
        "configKey": config_key
    }
    res = requests.post(url, data=data)
    r = res.json()
    return r


# 按id拉取
def apollo_id(config_id):
    url = f"{apolloUrl}{get_id}"
    data = {
        "configIds": [config_id]
    }
    headr = {"Content-Type": "application/json"}
    # 关闭不安全警告
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        res = requests.post(url, data=json.dumps(data), headers=headr, verify=False)
    except Exception as E:
        logging.warning(f"apollo request fail!,{E}, try again...")
        res = requests.post(url, data=json.dumps(data), headers=headr, verify=False)
    return res.json()


# 获取版本配置方式(静态,动态)
def version_config_switch(type):
    """
    type: [online,gray,daily] 线上,灰度,日报
    open: 开启动态
    close: 关闭动态
    stop: 停止运行
    """
    r = apollo("app_run_version")
    online = jsonpath.jsonpath(r, "$.data[0].content.online_config")[0]
    gray = jsonpath.jsonpath(r, "$.data[0].content.gray_config")[0]
    daily = jsonpath.jsonpath(r, "$.data[0].content.crash_daily_config")[0]

    def open_close(data):
        if data == "open":
            return True
        elif data == "close":
            return False

    if type == "online":
        return open_close(online)
    elif type == "gray":
        return open_close(gray)
    elif type == "daily":
        return open_close(daily)


# 获取运行开关
def stop_config(type):
    """
        type: [online,gray,daily] 线上,灰度,日报
        stop: 停止运行
        return: True:程序中止,不运行; False:正常执行
    """
    try:
        r = apollo("app_run_version")
    except Exception as E:
        logging.error(f"apollo stop_config request fail! {E}")
        return True
    online = jsonpath.jsonpath(r, "$.data[0].content.online_config")[0]
    gray = jsonpath.jsonpath(r, "$.data[0].content.gray_config")[0]
    daily = jsonpath.jsonpath(r, "$.data[0].content.crash_daily_config")[0]

    def stop(data):
        if data == "stop":
            return True
        else:
            return False

    if type == "online":
        return stop(online)
    elif type == "gray":
        return stop(gray)
    elif type == "daily":
        return stop(daily)


# 获取Bugly阈值配置
def get_bugly_threshold():
    crashdic = {}
    anrdic = {}
    errordic = {}
    try:
        r = apollo("bugly_threshold")

        crash = jsonpath.jsonpath(r, "$.data[0].content.crash")[0]
        crash = eval(crash)
        crashdic['Probability'] = float(crash['crash_rate']) * 100
        crashdic['Volatility'] = float(crash['crash_vibration_rate']) * 100
        crashdic['User'] = int(crash['crash_num'])

        anr = jsonpath.jsonpath(r, "$.data[0].content.anr")[0]
        anr = eval(anr)
        anrdic['Probability'] = float(anr['crash_rate']) * 100
        anrdic['Volatility'] = float(anr['crash_vibration_rate']) * 100
        anrdic['User'] = int(anr['crash_num'])

        error = jsonpath.jsonpath(r, "$.data[0].content.error")[0]
        error = eval(error)
        errordic['Probability'] = float(error['crash_rate']) * 100
        errordic['Volatility'] = float(error['crash_vibration_rate']) * 100
        errordic['User'] = int(error['crash_num'])
    except Exception as e:
        print(e)
        # 返回备用配置
        return crashdefault, anrdefault, errordefault

    return crashdic, anrdic, errordic


# 获取Crash日报取前几个版本数据
def get_top_version():
    r = apollo("bugly_threshold")
    if not r:
        return False
    top_version = jsonpath.jsonpath(r, "$.data[0].content.top_version")[0]
    return int(top_version)


# 获取线上监控版本数量
def get_online_top_version():
    r = apollo("bugly_threshold")
    if not r:
        return False
    top_version = jsonpath.jsonpath(r, "$.data[0].content.online_top_version")[0]
    return int(top_version)


# 获取灰度阈值配置
def get_gray_threshold():
    r = apollo("bugly_threshold")
    if not r:
        return False
    data = jsonpath.jsonpath(r, "$.data[0].content.gray_accessUser")[0]
    data = eval(data)
    max_access_user = data["max_accessUser"]
    min_access_user = data["min_accessUser"]

    return [int(max_access_user), int(min_access_user)]


# 获取版本号
def get_version(gray_with=1):
    """

    Args:
        gray_with: 1:返回所有版本号,True:返回灰度版本号,False:返回正式版本号

    Returns:

    """
    try:
        r = apollo("app_run_version")
        # print(r,"\n")
        data = jsonpath.jsonpath(r, "$.data[0].content.table")[0]
        # print(data)
        # 去除头尾中括号
        # data = re.search('(\{(.*)})',data).group()           # 去除头尾中括号[]
        data = str(data).strip("[]")
        # 把所有双引号改单引号,为了能用jsonpath读取数据
        data = data.replace("\"", "\'")
        data = data.replace("false", "\'false\'")
        data = data.replace("true", "\'true\'")
        # 转为字典/json格式
        data = eval(data)
        # print(data)
        version_list = []
        gray_version_list = []
        for num in range(len(data)):
            gray = jsonpath.jsonpath(data[num], "$.gray_switch")[0]
            if gray == 'true':
                gray_version_list.append(jsonpath.jsonpath(data[num], "$.app_version")[0])
            else:
                version_list.append(jsonpath.jsonpath(data[num], "$.app_version")[0])
        # print(version_list)
        # print(gray_version_list)
        if gray_with is False:
            return version_list
        elif gray_with is True:
            return gray_version_list
        else:
            version = {'version': version_list, 'gray_version': gray_version_list}
            return version
    # 异常情况,返回备用配置
    except Exception as e:
        print(e)
        if gray_with is True:
            return version_backup['gray_version']
        elif gray_with is False:
            return version_backup['version']
        else:
            return version_backup


# 获取阿波罗配置上的 jieba自定义词典,老版本tapd有引用
def load_jieba_config():
    r = apollo_id(2467)
    # 对数据进行转换,方便提取
    data = pd.Series(r)
    # 取自定义词典
    userdict = data['data'][0]['content']['keywords_config']['jieba_userdict']
    # 取转需关键字
    key_words = data['data'][0]['content']['keywords_config']['keywords']
    # 关键字csv
    with open("android_requirements.csv", "w", encoding="utf-8") as csv:
        csv.write(key_words)
        csv.close()
    # 自定义词典txt
    with open("userdict.txt", "w", encoding="utf-8") as f:
        f.write(userdict)
        f.close()
    # 读取自定义词典
    jieba.load_userdict("userdict.txt")
    return jieba, "android_requirements.csv"


def load_user_feedback_config(config_key, config_value):
    """
    owner_config: 处理人配置,value:owner
    status_config: 状态配置,value:status
    """
    r = apollo_id(2467)
    # 对数据进行转换,方便提取
    data = pd.Series(r)
    # 取自定义词典
    config_list = data['data'][0]['content'][config_key]
    config = []
    for conf in config_list:
        config.append(conf[config_value])
    return config


# 用反自动驳回阿波罗配置
class AutoForwardConfig:
    # 自动转发-公共配置
    class AutoForwardPublicConfig:
        def __init__(self):
            response = apollo_id(2704)
            self.data = pd.Series(response)

        @property
        def keywords(self):
            keyword_list = self.data['data'][0]['content']['keywords']
            keywords = []
            for key in keyword_list:
                keywords.append(key['keyword'])
            return keywords

        @property
        def describe(self):
            keyword_list = self.data['data'][0]['content']['keywords']
            describe = {}
            for key in keyword_list:
                describe[key['keyword']] = key['describe']
            return describe

        @property
        def second_keywords(self):
            keyword_list = self.data['data'][0]['content']['keywords']
            second_keywords = {}
            for key in keyword_list:
                second_keyword_list = key['second_keywords']  # 二级关键词列表
                if second_keyword_list[0]['keyword']:
                    tmp_second_keywords = []
                    for second in second_keyword_list:
                        tmp_second_keywords.append(second['keyword'])
                    second_keywords[key['keyword']] = tmp_second_keywords
            return second_keywords

        @property
        def stopwords(self):
            # 生成停用词配置
            tmp_stop_words = self.data['data'][0]['content']['stop_words']
            stop_words = []
            for word in tmp_stop_words:
                stop_words.append(word['word'])
            return stop_words

        def build_config(self):
            user_dict = self.keywords + self.stopwords
            with open("user_dict.txt", "w", encoding="utf-8") as f:
                f.writelines("\n".join(user_dict))
                f.close()

            with open("stopwords.txt", "w", encoding="utf-8") as f:
                f.writelines("\n".join(self.stopwords))
                f.close()

    # 自动转发-不同FT配置
    class AutoForwardFTConfig:
        def __init__(self):
            response = apollo_id(2703)
            self.data = pd.Series(response)
            self.ft_data = self.data['data'][0]['content']['ft_classification']
            # 公共配置
            self.public = AutoForwardConfig.AutoForwardPublicConfig()

        # FT匹配词
        @property
        def matching_ft_config(self):
            ft_matching_config = {}
            for data in self.ft_data:
                ft_matching_config[data['ft_name']] = (data['matching_ft'][0]['word'])
            return ft_matching_config  # {'驾车': '驾车', '公交': '公交', '基线': '基', '性能': '性能'}

        # 对应FT处理人
        @property
        def owners_config(self):
            owners = defaultdict(list)
            for data in self.ft_data:
                owner_list = data['owners']
                for owner in owner_list:
                    owners[data['ft_name']].append(owner['owner'])

            return owners  # {驾车：['ericlliu'], 公交：['jonnyxie'],...}

        # 关键词相关配置(关键词、描述、二级关键词)
        def keywords_config(self):
            keywords = defaultdict(list)
            describe = {}
            second_keywords = {}
            for data in self.ft_data:
                keyword_list = data['keywords']
                second_keywords[data['ft_name']] = []  # 初始化
                describe[data['ft_name']] = {}  # 初始化
                second_keywords[data['ft_name']] = {}  # 初始化
                for key in keyword_list:
                    # 关键词
                    keywords[data['ft_name']].append(key['keyword'])
                    # 描述信息
                    describe[data['ft_name']][key['keyword']] = key['describe']
                    # 二级关键词
                    second_keyword_list = key['second_keywords']
                    tmp_second_keyword_list = []
                    for second_key in second_keyword_list:
                        # 筛取二级关键词 不为空的
                        if second_key['keyword']:
                            tmp_second_keyword_list.append(second_key['keyword'])
                    if tmp_second_keyword_list:
                        second_keywords[data['ft_name']][key['keyword']] = tmp_second_keyword_list

            return keywords, describe, second_keywords

        # 生成配置文件
        def build_config(self):
            keywords, describe, second_keywords = self.keywords_config()
            ft_names = list(keywords.keys())

            for name in ft_names:

                keywords[name] = self.public.keywords + keywords[name]  # 与公共关键词合并
                keywords[name] = [s for s in keywords[name] if s != '']  # 剔除关键词中 空字符串

                describe[name] = {**describe[name], **self.public.describe}  # 与公共描述信息合并

                second_keywords[name] = {**second_keywords[name], **self.public.second_keywords}  # 与公共二级关键词合并

                # 将二级关键词合并入关键词中 生成自定义词典用于切词匹配
                merge_keywords = {}
                keyword_list = list(second_keywords[name].keys())
                for title in keyword_list:
                    title_keywords = second_keywords[name][title]
                    for word in title_keywords:
                        merge_keywords[word] = ''  # 用字典键不可重复性自动去重
                merge_keywords = list(merge_keywords.keys())  # 取键,即二级关键词
                merge_keywords = keywords[name] + merge_keywords  # 合并
                # 对合并后的词典列表再进行一次去重,并维持原顺序
                final_keywords = list(set(merge_keywords))
                final_keywords.sort(key=merge_keywords.index)
                # 与停用词词典合并
                final_keywords = self.public.stopwords + final_keywords

                # 生成jieba自定义词典
                with open(f"{name}-userdict.txt", "w", encoding="utf-8") as f:
                    f.writelines('\n'.join(final_keywords))
                    f.close()

                # 生成关键词csv
                with open(f"{name}-keywords.csv", "w", encoding="utf-8") as f:
                    f.writelines('\n'.join(keywords[name]))
                    f.close()

                # 生成二级关键词csv
                header = (list(second_keywords[name].keys()))  # 写入csv的标题
                lens = []  # 列表长度
                current_second_keywords = []
                for key in header:
                    current_second_keywords.append(second_keywords[name][key])
                    lens.append(len(second_keywords[name][key]))
                max_len = max(lens)  # 最大长度

                rows = []  # 写入csv的行内容
                for l in range(0, max_len):
                    row = []
                    for i in range(len(current_second_keywords)):
                        if l >= len(current_second_keywords[i]):
                            row.append(None)
                            continue
                        row.append(current_second_keywords[i][l])
                    rows.append(row)

                with open(f"{name}-second_keywords.csv", "w", encoding="utf-8") as f:
                    f_csv = csv.writer(f)  # 创建csv文件写入句柄
                    f_csv.writerow(header)  # 写入标题
                    f_csv.writerows(rows)  # 写入内容
                    f.close()

                # 停用词
                with open(f"stopwords.txt", "w", encoding="utf-8") as f:
                    f.writelines('\n'.join(self.public.stopwords))
                    f.close()

        # 描述信息
        @property
        def describe(self):
            keywords, describe, second_keywords = self.keywords_config()

            ft_names = list(keywords.keys())

            for name in ft_names:

                if not keywords[name]:
                    continue

                # 生成描述信息
                if describe[name]:
                    tmp_trash_can = []  # 临时垃圾桶
                    for key in describe[name]:
                        if not describe[name][key]:
                            tmp_trash_can.append(key)
                    for trash in tmp_trash_can:
                        del describe[name][trash]  # 剔除没有描述信息的关键词
            return describe

        # 停用词
        @property
        def stopwords(self):
            return "stopwords.txt"

    # 匹配FT,返回对应配置文件
    class FTConfig:
        def __init__(self, ft_name):
            self.ft_name = ft_name

        # 处理人
        @property
        def owner(self):
            owners = AutoForwardConfig().AutoForwardFTConfig().owners_config
            return owners[self.ft_name]  # {驾车：['ericlliu','lisi']}

        # 自定义词库
        @property
        def userdict(self):
            return f"{self.ft_name}-userdict.txt"

        # 关键词配置
        @property
        def keywords(self):
            return f"{self.ft_name}-keywords.csv"

        # 二级关键词配置
        @property
        def second_keywords(self):
            return f"{self.ft_name}-second_keywords.csv"
