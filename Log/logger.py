# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import sys, os

parPath = os.path.abspath("..")
sys.path.append(parPath)

# -------------------加入当前工作父目录,防止找不到模块的报错----------------------------
import logging
import colorlog


def logg(filename):
    # 实例化logger对象
    logger = logging.getLogger()

    # 设置日志级别
    logger.setLevel(level=logging.INFO)

    log_colors_config = {
        'INFO': 'green',  # cyan white
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
    # 向控制台输出
    color_fmt = "%(log_color)s%(asctime)s - %(filename)s [line:%(lineno)d] - %(levelname)s: %(message)s"
    console = logging.StreamHandler()
    console_format = colorlog.ColoredFormatter(color_fmt, log_colors=log_colors_config)
    console.setFormatter(console_format)

    # 向文件输出
    outfile = logging.FileHandler(filename=filename, encoding="utf-8")
    # 设置日志输出格式
    fmt = "%(asctime)s - %(filename)s [line:%(lineno)d] - %(levelname)s: %(message)s"
    outfile_format = logging.Formatter(fmt)
    outfile.setFormatter(outfile_format)

    # 把对象加入到logger里
    logger.addHandler(console)
    logger.addHandler(outfile)

    # 移除句柄，避免重复打印
    # logger.removeHandler(console)
    # logger.removeHandler(outfile)

    # 关闭打开的文件
    console.close()
    outfile.close()
