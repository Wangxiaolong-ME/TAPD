import logging
import os
import sys
import time

from Tapd.Util.normal_util import millisecond
from RobotMessage.robot_config import key_crash
from RobotMessage.robot_message import robot_message
from Tapd.Module.xlog_module import XlogModule
from Tapd.Module.xlog_module import CrashXlogModule
from Tapd.Module.xlog_module import DecodeModule
from Tapd.Config import config
from Tapd.Util.xlog_util import save_data_to_file
from Tapd.Util.xlog_util import unzip_file
from Tapd.Module.tapd_module import TapdModule

sys.path.append('..')


def xlog_module(entity):
    logging.info(" ========== xlog_module running .... ========== ")

    point = {}  # xlog 埋点

    owner_list = entity.keys()
    for current_owner in owner_list:

        logging.info(f"当前处理人: {current_owner}")

        if not entity[current_owner]:
            logging.warning(f"当前处理人:{current_owner}用反数量 0")
            continue

        entry_id_list = entity[current_owner].keys()

        if entry_id_list:
            for entry_id in entry_id_list:
                data = entity[current_owner][entry_id]

                xlog = XlogModule(data)  # 实例化Xlog业务模块

                logging.info(f"Xlog_module Start bug_id: {data.bug_id}")

                comment = TapdModule.CommentModule(entry_id)  # 评论模块
                comment_result = comment.judge_by_comment("xlog")  # 根据评论内容判断xlog是否已上传
                if comment_result is False:  # 没有历史上传评论

                    begin_time = time.time()  # xlog 处理开始时间点

                    # maplog平台查询xlog
                    logging.info("Searching xlog....")
                    file_url = xlog.search_xlog_module()  # fileUrl,xlog下载入参
                    if file_url == 0:  # 查询状态正常,但没有日志上传记录
                        xlog_null = comment.judge_by_comment("xlog_null")
                        # 若之前没有添加日志无记录的评论,此次为首次添加
                        if xlog_null is False:
                            comment.add_comment("xlog_null")  # 添加 未查询到xlog评论
                        continue
                    elif not file_url:
                        continue

                    # 下载xlog
                    logging.info("Downloading xlog....")
                    response = xlog.download_xlog_module(file_url)
                    if not response:
                        continue

                    dir_path = f"{config.save_path}/{entry_id}"  # xlog保存目录路径

                    # 保存xlog
                    save_data_result = save_data_to_file(response.content, dir_path + ".zip")
                    if not save_data_result:
                        continue

                    # 解压xlog
                    unzip = unzip_file(dir_path + ".zip", dir_path)
                    if not unzip:
                        continue

                    os.remove(dir_path + ".zip")  # 解压后 删除原压缩文件

                    # 解析xlog
                    logging.info("Decoding xlog....")
                    decode = DecodeModule(dir_path, data.back_time[0])  # 实例化解析实体
                    decode.decode()  # 执行解析,对当前entry_id目录下文件进行解析

                    crash = CrashXlogModule(dir_path)  # 检索crash模块

                    # 检查是否有xcrash日志文件
                    xcrash, xcrash_text = crash.xcrash()

                    # 检索crash关键词
                    crash_keyword = crash.retrieval_crash_keywords()

                    crash_type = None

                    # 上传xlog
                    logging.info(f"Uploading xlog....")
                    xlog_result = xlog.upload_xlog_module(dir_path)  # 上传结果

                    # 上传成功
                    if xlog_result:
                        comment.add_comment("xlog")  # 添加 xlog日志已上传评论

                        if xcrash:
                            comment.add_comment("xcrash")  # 添加 xcrash评论
                            comment.add_comment("extend", xcrash_text)  # 添加 xcrash日志内容 评论

                            robot_message(
                                f"<@{current_owner}>\n{data.title}\n{data.url}\n{config.comment_text['xcrash']}",
                                key_crash)  # 发送群消息
                            crash_type = "xcrash"  # xcrash 类型埋点

                        elif crash_keyword:
                            comment.add_comment("extend", crash_keyword[0])  # 添加 crash关键词评论
                            robot_message(
                                f"<@{current_owner}>\n{data.title}\n{data.url}\n{crash_keyword[0]}", key_crash)  # 发送群消息
                            crash_type = crash_keyword[1]  # crash 关键词埋点

                    end_time = time.time()  # xlog 处理结束时间点
                    total_time = millisecond(end_time, begin_time)  # 处理耗时,单位:毫秒

                    point[entry_id] = {
                        "bug_id": data.bug_id,
                        "title": data.title,
                        "url": data.url,
                        "first_class": data.first_class,
                        "platform": data.platform,
                        "version": data.version[0],
                        "phone_model": data.phone_model,
                        "xlog_run_time": total_time,
                        "crash_type": crash_type,
                    }

                    logging.info(f"Xlog_module Finished! total_time: {total_time}ms, bug_id: {data.bug_id}\n")
                logging.info(f"Xlog_module Finished! bug_id: {data.bug_id}\n")
    # 输出日志内容:此次过程处理了多少条xlog
    xlog_num = len(point.keys())
    logging.info(f"Xlog_module:deal with {xlog_num} xlog in this process")
    return point
