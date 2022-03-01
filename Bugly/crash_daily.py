import datetime
import sys
import time

sys.path.append("..")
import Bugly.bugly_config
from Bugly.bugly import local_get_version, sort_by_access, daily_bugly
from Bugly.bugly_config import log
from Apollo.apollo_api import stop_config, get_top_version, version_config_switch
from Bugly.gray_crash import get_gray_version
from RobotMessage.robot_config import key_android_crash
from RobotMessage.robot_message import robot_message

log()

message = []
localtime = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def main():
    version_list = local_get_version()  # [[纯版本],[版本号,活跃设备数]]

    if not version_list:
        # 重试获取
        time.sleep(10)
        version_list = local_get_version()
        if not version_list:
            sys.exit(1)  # 异常退出

    versions = sort_by_access(version_list[1])  # 按照活跃设备数排序
    gray_version = get_gray_version()  # 获取灰度版本号

    top_version = get_top_version()  # 获取top_version
    # 静态,动态配置版本方式 可切换
    online_switch = version_config_switch("daily")

    """
    没有获取到版本的情况或开关切换到静态模式时,使用静态配置
    对静态配置的版本号也进行活跃设备数排序
    """
    if not versions or not online_switch:
        version_dict = dict(sort_by_access(version_list[1], only_version=False, all_version=False))  # 获取版本,活跃数 转换为字典
        versions = Bugly.bugly_config.online_versions  # 静态配置的版本号
        # 获取版本号的活跃设备数,进行排序
        version_access = []
        for ver in versions:
            version_access.append([ver, version_dict[ver]])
        versions = sort_by_access(version_access, all_version=False)  # 按活跃数排序版本

        # 对灰度版本也进行排序,仅取一个最大活跃数的版本
        if gray_version:
            gray_version_access = []
            for ver in gray_version:
                gray_version_access.append([ver, version_dict[ver]])
            gray_versions = sort_by_access(gray_version_access, all_version=False)  # 按活跃数排序灰度版本
            versions = [gray_versions[0]] + versions  # 静态模式,线上版本不会包含灰度版本,取一个最大活跃数的灰度版本添加进所有版本中

        versions.insert(0, '-1')  # 并且静态模式没有全版本,这里添加全版本

    """ 获取监控的版本数量 """
    if not top_version:
        top_version = Bugly.bugly_config.crash_daily_top_version  # 获取默认配置,前5个

    versions = versions[0:top_version]

    for v in range(top_version):
        if versions[v] == '-1':
            version = '全版本'
            describe = ""
        else:
            if not gray_version:  # 灰度版本为空
                version = versions[v]
                describe = ""
            elif versions[v] in gray_version:
                version = gray_version
                if type(gray_version) is list:
                    version = gray_version[gray_version.index(versions[v])]
                describe = "(🛠灰度版本)"
            else:
                version = versions[v]
                describe = ""

        # crash设备
        crash_data = daily_bugly(1, versions[v])
        # anr设备
        anr_data = daily_bugly(2, versions[v])
        # crash率、anr率
        crash_pr = (crash_data[1] / crash_data[2])
        anr_pr = (anr_data[1] / anr_data[2])
        probability = [round(crash_pr * 100, 3), round(anr_pr * 100, 3)]

        tmp_message = f"{version} {describe}\nCrash次数: {crash_data[0]}" \
                      f"\nCrash设备数: {crash_data[1]}" \
                      f"\n活跃设备数: {crash_data[2]}" \
                      f"\n用户Crash率: {probability[0]}%" \
                      f"\nAnr设备数: {anr_data[1]}" \
                      f"\n用户Anr率: {probability[1]}%\n"
        global message
        if describe == "(🛠灰度版本)":
            message.insert(1, tmp_message)
        else:
            message.append(tmp_message)


if __name__ == '__main__':
    # 是否执行程序
    stop = stop_config("daily")
    if stop:
        print("阿波罗配置程序停止,程序正常中止!")
        sys.exit()
    main()
    message.insert(0, f"{localtime} Crash日报\n")

    message = '\n'.join(message)
    robot_message(message, key_android_crash)
