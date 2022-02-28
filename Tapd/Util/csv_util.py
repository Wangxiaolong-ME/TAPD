import logging
import os
import shutil
import sys

from selenium import webdriver

from Tapd.Config import config

sys.path.append('..')
sign = config.sign


# 移动csv_download目录下的文件到csv_save下
def rename(source_file, new_file):
    try:
        shutil.move(fr"{source_file}", fr"{new_file}")
    except Exception as e:
        logging.warning(f"Csv_Module move, Exception info:{e}")


# 程序运行前检查存放目录是否为空，不为空删除目录下的文件
def remove_csv_download():
    try:
        if os.path.exists(config.csv_download) is True:
            filelist = os.listdir(config.csv_download)  # 遍历目录下的所有文件
            if filelist:
                for file in filelist:
                    os.remove(fr"{config.csv_download}{sign}{file}")
                logging.info("Csv_download_directory is clear!")
        else:
            os.makedirs(config.csv_download)
    except Exception as E:
        logging.error(f"remove_csv_download except: {E}")


# selenium 配置启动参数
def driver_options():
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": config.csv_download}
    options.add_experimental_option("prefs", prefs)
    # 如果平台是windows, 使用无头模式
    if sign == "\\":
        options.add_argument("--headless")
    options.add_argument('blink-settings=imagesEnabled=false')
    options.add_argument('--no-sandbox')    # 解决DevToolsActivePort文件不存在的报错
    return options
