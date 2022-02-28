import logging
import os
import platform
import sys
import time
from time import sleep

import func_timeout
from func_timeout import func_set_timeout
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Tapd.Config import config
from Tapd.Module.tapd_module import TapdModule
from Tapd.Util.csv_util import driver_options, rename, remove_csv_download
from Tapd.Util.normal_util import millisecond, file_or_dir, get_file_size

sys.path.append('..')
sign = config.sign


def csv_upload_module(entry_id, dir_path):
    file_type = file_or_dir(dir_path)  # 判断文件类型(目录/文件)
    tapd = TapdModule.UploadModule(entry_id)  # TAPD上传附件模块

    if file_type:  # 目录
        directory = os.listdir(dir_path)
        dir_path = dir_path + "/" + directory[0]

    log_file_list = os.listdir(dir_path)

    for log in log_file_list:
        log_path = dir_path + sign + log

        lof_size = get_file_size(log_path)

        if lof_size < 1:
            logging.warning(f"Csv_Upload_Module: {log} size is too small!")
            return False

        upload = tapd.upload(log, log_path)  # 上传csv

        if upload:
            return True
        else:
            logging.warning(f"Csv_Upload_Module: {log} upload fail! entry_id: {entry_id}")
            return False


@func_set_timeout(7200)  # csv模块超时为120分钟
def csv_module(entity):
    logging.info(" ========== csv_module running .... ========== ")

    # options = driver_options()  # selenium 前置配置
    # driver = webdriver.Chrome(options=options)  # 实例化selenium
    # driver.implicitly_wait(10)

    tapd = TapdModule()  # TAPD模块
    point = {}  # csv埋点

    # 填入的开始、结束时间的正确次数,计算有效占比
    time_proportion = {
        "total": 0,
        "start_time": 0,
        "end_time": 0
    }

    owner_list = entity.keys()
    for current_owner in owner_list:
        logging.info(f"当前处理人: {current_owner}")

        if not entity[current_owner]:
            logging.warning(f"当前处理人:{current_owner}用反数量 0")
            continue

        entry_id_list = entity[current_owner].keys()
        if entry_id_list:
            # chrome_run_number = 0  # 浏览器运行次数
            options = driver_options()  # selenium 前置配置
            driver = webdriver.Chrome(options=options)  # 实例化selenium
            driver.implicitly_wait(10)
            for entry_id in entry_id_list:
                try:
                    driver.quit()
                    remove_csv_download()  # 判断csv_download目录是否存在,并清空

                    # if chrome_run_number == 10:
                    #     driver.quit()
                    #     options = driver_options()  # selenium 前置配置
                    #     driver = webdriver.Chrome(options=options)  # 实例化selenium
                    #     driver.implicitly_wait(10)

                    options = driver_options()  # selenium 前置配置
                    driver = webdriver.Chrome(options=options)  # 实例化selenium
                    driver.implicitly_wait(10)

                    data = entity[current_owner][entry_id]

                    # 访问灯塔URL,点击IOA快速登录
                    if data.platform == "Android":
                        url = config.csv_android_url
                    else:
                        url = config.csv_ios_url

                    comment = tapd.CommentModule(entry_id)  # TAPD中的评论模块

                    if comment.judge_by_comment("csv") is True:  # True,历史上传过csv日志
                        continue

                    begin_time = time.time()  # 开始时间点

                    logging.info(f"Csv_Module Start bug_id: {data.bug_id}")

                    driver.get(url)

                    try:
                        page = driver.page_source  # 页面源码
                        if "iOA 快速登录" in page:  # 判断当前页面是否是IOA登录页面
                            # ioa登录点击确认
                            ioa = driver.find_element_by_xpath("//input[@id='btn_smartlogin']")
                            ioa.click()
                            driver.get(url)
                    except Exception as E:
                        logging.warning(f"Csv_Module (ioa_click) Exception, {E}")
                        continue

                    sleep(2)

                    # 输入开始和结束时间
                    try:
                        start_time = driver.find_element(By.XPATH, "//input[@placeholder='开始日期']")
                        end_time = driver.find_element(By.XPATH, "//input[@placeholder='结束日期']")

                        system_name = platform.system()  # 操作系统
                        if system_name == "Windows":
                            keys = Keys.CONTROL
                        else:
                            keys = Keys.COMMAND

                        try:
                            start_time.click()
                        except Exception:
                            driver.execute_script("$(arguments[0]).click()", start_time)

                        sleep(2)

                        start_time.send_keys(keys + "a")
                        sleep(2)
                        start_time.send_keys(f"{data.back_time[1]}")
                        sleep(2)

                        end_time.send_keys(keys + "a")
                        sleep(2)
                        end_time.send_keys(f"{data.back_time[2]}")
                        sleep(2)
                        driver.find_element_by_xpath(
                            "//div[@class='el-picker-panel__footer']//span[contains(text(),'确定')]").click()

                        # 输出开始和结束时间和输入的开始和结束时间,用于排查实际输入是否正确
                        logging.info(f"start_time is {data.back_time[1]}, end_time is {data.back_time[2]}")
                        logging.info(f"input start_time is {start_time.get_attribute('value')}")
                        logging.info(f"input end_time is {end_time.get_attribute('value')}")

                        time_proportion["total"] += 1  # 填入时间的TAPD总个数
                        # 开始、结束时间填入的有效占比
                        if start_time.get_attribute("value") == data.back_time[1]:
                            time_proportion["start_time"] += 1

                        if end_time.get_attribute("value") == data.back_time[2]:
                            time_proportion["end_time"] += 1

                    except Exception as e:
                        logging.warning(f"Csv_Module (begin_end_time) Exception, Info:{e}")
                        continue

                    try:
                        # 事件下拉框
                        select = driver.find_element_by_xpath("//input[@placeholder='请选择']")
                        # 此方法点击解决会有元素覆盖的情况
                        driver.execute_script("$(arguments[0]).click()", select)
                        sleep(3)
                        # 选择QIMEI
                        select_qimei = driver.find_element_by_xpath("//span[text()='QIMEI']")
                        select_qimei.click()
                    except Exception as e:
                        logging.error(f"Csv_Module (select_qimei) Exception, Info:{e}")
                        continue

                    try:
                        # 输入qimei
                        input_qimei = driver.find_element_by_xpath("//input[@placeholder='请输入完整的QIMEI']")
                        input_qimei.send_keys(f"{data.qimei}")
                    except Exception as e:
                        logging.warning(f"Csv_Module (input_qimei) Exception, Info:{e}")
                        continue

                    @func_set_timeout(180)  # 设置超时阈值为3分钟
                    def search_download():  # 检索并下载
                        try:
                            # 检索
                            search_btn = driver.find_element_by_xpath("//span[text()=' 检索日志 ']")
                            driver.execute_script("$(arguments[0]).click()", search_btn)
                        except Exception as e:
                            logging.warning(f"Csv_Module (search_btn) Exception, Info:{e}")
                            return False
                        try:
                            # 判断当前检索日志是否完成,设置超时为2分钟
                            for i in range(1, 20):
                                sleep(6)
                                page = driver.page_source
                                if "app版本" in page:
                                    break
                        except Exception as E:
                            logging.warning(f"Csv_Module (page_source) Exception, {E}")
                            return False

                        try:
                            # 下载
                            logging.info(f"Csv_Module Downloading....")
                            download_btn = driver.find_element(By.XPATH,
                                                               "//a[text()='下载Excel']")
                            # driver.execute_script("$(arguments[0]).click()", download_btn)
                            download_btn.click()
                        except Exception as e:
                            logging.warning(f"Csv_Download Exception, Info: {e}, bug_id:{data.bug_id}")
                            return False

                        return True

                    try:
                        result = search_download()  # 执行检索下载
                        if not result:
                            continue
                    except func_timeout.exceptions.FunctionTimedOut:
                        logging.warning("search_download timeout,continue...")
                        continue

                    sleep(2)

                    try:
                        file_list = os.listdir(config.csv_download)
                        if not file_list:
                            logging.error(f"Csv_Save Fail, bug_id:{data.bug_id}")
                            continue
                        for file in file_list:
                            if file.endswith(".csv"):
                                source_file = config.csv_download + sign + file
                                new_file = config.csv_download + sign + entry_id + ".csv"
                                rename(source_file, new_file)  # 移动到csv_save目录下
                    except Exception as e:
                        logging.warning(f"Csv_Module Exception, Info:{e}")
                        continue

                    # 上传csv
                    logging.info(f"Csv_Module Uploading....")
                    csv_upload = csv_upload_module(entry_id, config.csv_download)
                    if not csv_upload:
                        continue

                    # 添加csv上传评论
                    comment.add_comment("csv")

                    endtime = time.time()  # 结束时间点
                    total_time = millisecond(begin_time, endtime)  # 耗时

                    # csv埋点
                    point[entry_id] = {
                        "bug_id": data.bug_id,
                        "title": data.title,
                        "url": data.url,
                        "first_class": data.first_class,
                        "platform": data.platform,
                        "version": data.version[0],
                        "phone_model": data.phone_model,
                        "csv_run_time": total_time,
                    }

                    logging.info(f"Csv_Module Finished! total_time: {total_time}ms, bug_id: {data.bug_id}\n")
                    # chrome_run_number = chrome_run_number + 1
                except Exception as E:
                    logging.warning(f"Csv_Module Exception, {E}")

    if time_proportion["total"]:
        logging.info(f"time_total: {time_proportion['total']}")

        if time_proportion["start_time"]:
            start_time_proportion = round(time_proportion["start_time"] / time_proportion["total"], 2) * 100
            logging.info(f"start_time_proportion: {start_time_proportion}%")

        if time_proportion["end_time"]:
            end_time_proportion = round(time_proportion["end_time"] / time_proportion["total"], 2) * 100
            logging.info(f"end_time_proportion: {end_time_proportion}%")

    else:
        logging.warning(f"start: {time_proportion['start_time']}, "
                        f"end: {time_proportion['end_time']}")
    # 输出日志内容:此次过程处理了多少条csv
    csv_num = len(point.keys())
    logging.info(f"Csv_module:deal with {csv_num} csv in this process")
    return point
