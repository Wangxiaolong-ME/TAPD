import logging
import sys

import func_timeout

sys.path.append('../..')
from Log.logger import logg
from Tapd.Module.atta_module import AttaModule
from Tapd.Module.tapd_csv_module import csv_module
from Tapd.Module.tapd_forward_module import forward_module
from Tapd.Module.tapd_module import TapdModule
from Tapd.Module.tapd_xlog_module import xlog_module
from Tapd.Util.point_util import MergeDict
from Tapd.Util.normal_util import output_summary_information

logg("tapd_xlog.log")

if __name__ == '__main__':
    tapd_module = TapdModule.TapdInfoModule()  # TAPD信息模块
    total_entity = tapd_module.get_total_tapd_module()  # 获取所有tapd信息

    forward_point = forward_module(total_entity)  # 自动流转模块

    xlog_point = xlog_module(total_entity)  # xlog模块

    try:
        csv_point = csv_module(total_entity)  # csv模块
    except func_timeout.exceptions.FunctionTimedOut:
        logging.error("csv_module process timeout!")
        csv_point = None

    # 输出埋点日志
    logging.info(f"forward_point:\n{forward_point}")
    logging.info(f"xlog_point:\n{xlog_point}")
    logging.info(f"csv_point:\n{csv_point}")

    merge = MergeDict()
    point = merge.merge_point([forward_point, xlog_point, csv_point])  # 合并所有埋点

    # 输出合并后的埋点日志
    logging.info(f"merge_point:\n{point}")

    atta = AttaModule(point)  # 上报埋点模块
    atta.report()  # 上报埋点

    output_summary_information(total_entity, point)  # 输出汇总信息,共获取多少tapd,处理多少tapd
