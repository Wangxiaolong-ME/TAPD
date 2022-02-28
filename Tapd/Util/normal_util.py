import datetime
import logging
import os
import re
import sys

import pandas as pd

sys.path.append('..')


def file_or_dir(path):
    file_dir = os.listdir(path)  # ['xlog','xlog','AnalysisLog','...']
    for file in file_dir:
        if os.path.isdir(f"{path}/{file}") is True:
            return True  # 是目录
        else:
            return False  # 是文件


def reg_time(_str):
    """ _Str: com.tencent.sosomap_20220102.xlog ---> 20220102"""
    reg = re.search("[0-9]{8}", _str)
    if reg:
        return reg.group()
    else:
        return None


def format_date(time_str):
    """
    time_str: 2021-12-10 10:05:00(str) ---> 2021-12-10(datetime)
    time_str: 20211210(str) ---> 2021-12-10(datetime)
    """
    reg = re.search(r"\d+-\d+-\d+", time_str)
    if reg:
        datetime_str = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").date()
    else:
        datetime_str = datetime.datetime.strptime(time_str, "%Y%m%d").date()
    return datetime_str


def millisecond(begin_time, endtime):
    # 如果开始时间结束时间输入先后顺序有误，调换
    if begin_time > endtime:
        t = begin_time
        begin_time = endtime
        endtime = t
    begin_time = begin_time * 1000
    endtime = endtime * 1000
    tot_time = round(endtime - begin_time, 2)
    return float(tot_time)


# 判断目录是否存在,不存在创建
def exists_dir(dir_path):
    # 判断目录是否存在
    if not os.path.exists(dir_path):
        # 目录不存在创建，makedirs可以创建多级目录
        os.makedirs(dir_path)


# 获取文件大小
def get_file_size(file_path):
    """ file_path: 文件路径 """
    size = round(os.path.getsize(file_path) / 1024, 2)  # 单位:KB
    return size


def output_summary_information(entity, point):
    # 已处理的用反数量
    if not point:
        processed = 0
    else:
        processed = len(point.keys())

    # 本次总共获取到的用反数量
    total_tapd_num = 0
    owner_list = entity.keys()
    for owner in owner_list:
        if entity[owner]:
            entry_id_list = entity[owner].keys()

            entry_id_len = len(entry_id_list)

            total_tapd_num = total_tapd_num + entry_id_len

    logging.info(f"There are {total_tapd_num} user feedback")  # 共有total条用户反馈
    logging.info(f"Total of {processed} user feedback were processed this time!")  # 已处理processed条用户反馈


# 读取csv文件，返回数据集，列，行
def read_csv_file(csv_file):
    dataset = pd.read_csv(csv_file)
    # 列
    columns = dataset.columns
    # 行
    index = dataset.index
    return dataset, columns, index
