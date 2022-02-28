# coding=utf-8
import datetime
import logging
import os
import subprocess

from Tapd.Config import crash_keywords
from Tapd.Module.tapd_module import TapdModule
from Tapd.Util.normal_util import file_or_dir, format_date
from Tapd.Util.xlog_util import get_file_url, get_xlog_endswith_date, get_last_two_days_xlog, read_lines
from Tapd.Service.xlog_service import XlogApi


class XlogModule(XlogApi):

    def __init__(self, entry_id_data):
        """
        entry_id_data: 单条entry_id下的data集合
        """
        super().__init__()
        self.qimei = entry_id_data.qimei
        self.bug_id = entry_id_data.bug_id
        self.entry_id = entry_id_data.entry_id
        self.back_time = entry_id_data.back_time

    def search_xlog_module(self):
        """
        return: 下载需要的入参 : file_url
        """

        if not self.qimei:
            logging.warning(f"bug_id: {self.bug_id} qimei为空!")
            return False
        begin_stamp = self.back_time[3]
        end_stamp = self.back_time[4]
        response = self.search_xlog(self.qimei, begin_stamp, end_stamp)
        if response:
            file_url = get_file_url(response.json())
            if file_url:
                return file_url
            else:
                logging.warning(f"search_xlog is None! bug_id: {self.bug_id}")
                return 0
        else:
            logging.warning(f"search_xlog fail! bug_id: {self.bug_id}")
            return False

    def download_xlog_module(self, file_url):
        response = self.download_xlog(file_url)
        if response:
            return response
        else:
            logging.warning(f"download_xlog fail! bug_id: {self.bug_id}")
            return False

    def upload_xlog_module(self, dir_path):
        tapd = TapdModule.UploadModule(self.entry_id)  # tapd上传附件模块

        file_type = file_or_dir(dir_path)  # 判断文件类型(目录/文件)

        if file_type:  # 目录
            directory = os.listdir(dir_path)
            dir_path = dir_path + "/" + directory[0]

        log_file_list = os.listdir(dir_path)
        result = 0  # 记录成功上传日志次数

        for log in log_file_list:
            log_path = dir_path + "/" + log
            log_size = round(os.path.getsize(log_path) / 1024, 2)  # 日志文件大小，KB
            reason = tapd.upload(log, log_path)
            if not reason:
                logging.warning(f"{log},size:{log_size}KB Upload Fail!")
            result = result + 1

        if result > 0:
            return True
        return False


class DecodeModule:
    """ file_path: ./save_path/1010118351093410535 """

    def __init__(self, dir_path, back_time):
        self.dir_path = dir_path
        self.back_time = format_date(back_time)

    def decode(self):
        file_type = file_or_dir(self.dir_path)  # 判断文件类型(目录/文件)

        if file_type:  # 目录
            dir_list = os.listdir(self.dir_path)
            self.dir_path = self.dir_path + "/" + dir_list[0]

        log_files = os.listdir(self.dir_path)

        xlog_dict = get_xlog_endswith_date(log_files)  # 取xlog日志对应时间的字典
        xlog_files = list(xlog_dict.keys())  # xlog文件名称列表

        last_two_date = self.back_time - datetime.timedelta(days=1)  # 反馈时间近几天
        last_two_days_xlog = get_last_two_days_xlog(xlog_dict, last_two_date)  # 近几天的xlog日志

        for xlog in xlog_files:

            xlog_path = self.dir_path + "/" + xlog

            if xlog not in last_two_days_xlog:
                os.remove(xlog_path)  # 删除2天之前的xlog文件,不解析
                continue

            try:
                decode_worker = subprocess.Popen("python2 ../Util/decode_log_util.py %s" % xlog_path, shell=True)
                if decode_worker.wait() == 0:
                    os.remove(xlog_path)  # 删除原加密文件
                else:
                    logging.warning(f"{xlog_path} decode fail!")
            except Exception as E:
                logging.exception(f"decode_worker filed!,except:{E}")


class CrashXlogModule:
    def __init__(self, dir_path):
        self.dir_path = dir_path

    def xcrash(self):
        """ 检索日志文件中是否有后缀为xcrash的文件 """
        file_type = file_or_dir(self.dir_path)  # 判断文件类型(目录/文件)

        if file_type:  # 目录
            dir_list = os.listdir(self.dir_path)
            self.dir_path = self.dir_path + "/" + dir_list[0]

        log_files = os.listdir(self.dir_path)
        log_files.sort(reverse=True)

        for log in log_files:
            if log.endswith(".xcrash"):
                # 绝对路径
                xcrash_path = self.dir_path + "/" + log
                # 读取xcrash日志部分内容，返回html格式文本，用于添加评论
                html_text = read_lines(xcrash_path)
                return True, html_text
        return False, "无xcrash"

    def retrieval_crash_keywords(self):
        """ 检索崩溃关键词 """
        file_type = file_or_dir(self.dir_path)  # 判断文件类型(目录/文件)

        if file_type:  # 目录
            dir_list = os.listdir(self.dir_path)
            self.dir_path = self.dir_path + "/" + dir_list[0]

        log_files = os.listdir(self.dir_path)

        crash_log = {}
        for log in log_files:
            crash_log[log] = {}

            if log.endswith(".log"):
                log_path = self.dir_path + "/" + log

                with open(log_path, encoding="ISO-8859-1") as file:
                    log_info = file.read()
                    file.close()

                    for word in crash_keywords.keywords:  # 依次用每一个关键词去匹配日志内容
                        if word in log_info:
                            crash_log[log][word] = f"{log_info.count(word)}次"
                        else:
                            continue

        message = []
        crash_point = ""

        for log in log_files:
            crash = crash_log[log].keys()  # crash关键词

            if not crash:  # 没有crash关键词,跳过
                continue

            crash = list(crash)
            crash_point = ",".join(crash)

            text = []
            key_word = crash

            for word in key_word:
                text.append(f"{word}: {crash_log[log][word]}")

            text = ",".join(text)
            message.append(f"用反机器人遍历日志{log}中出现报错关键词:{text}")

        if message:
            message = "\n".join(message)
            return [message, crash_point]
        else:
            return None
