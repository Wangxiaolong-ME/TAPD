import datetime
import re
import sys
import time


sys.path.append('..')


class TapdUtil:
    def __init__(self, description):
        self.des = description

    # 取正则中的文本
    def get_text(self, length, reg):
        if reg is not None and len(reg.group()) >= length:
            text = reg.group()
            text = re.search('[\S].*', text).group()  # 去除开头空格
            return text
        else:
            return False

    def qimei(self):
        reg_1 = re.search('(?<=qimei:).*?(?=[<>/?])', self.des)
        reg_2 = re.search('(?<=QIMEI36:).*?(?=[<>/?])', self.des)
        reg_3 = re.search('(?<=QIMEI:).*?(?=[<>/?])', self.des)

        # 第一种情况
        qimei = self.get_text(5, reg_1)
        if qimei:
            return qimei
        else:
            # 第二种情况
            qimei = self.get_text(5, reg_2)
            if qimei:
                return qimei
            else:
                # 第三种情况
                qimei = self.get_text(5, reg_3)
                if qimei:
                    return qimei
                else:
                    return None

    def version(self):
        # version匹配
        version_regex = re.search('([7-9][\.])([0-9]*\.)+[0-9]*', self.des)

        # 版本号获取
        version = self.get_text(2, version_regex)
        if version:
            version_1 = re.search('[0-9](?=\.)*', version).group()
            version_2 = re.search('(?<=\.)[0-9]*', version).group()
            return [version, version_1, version_2]

        else:
            return [9.17, 9, 17]

    def phone_model(self):
        # 手机型号匹配
        phone_model_regex = re.search('(?<=手机型号:).*?(?=[<>/?])', self.des)
        # 手机型号获取
        phone_model = self.get_text(2, phone_model_regex)
        if phone_model:
            return phone_model
        else:
            return None

    def back_time(self):
        # 时间匹配
        backtime_regex = re.search('([0-9]*\-){2}[0-9]* ([0-9]*\:){2}[0-9]*', self.des)
        time_str = self.get_text(5, backtime_regex)
        if time_str:
            back_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            one_day = datetime.timedelta(days=1)
            begintime = back_time.replace(hour=0, minute=0, second=0) - one_day
            endtime = back_time.replace(hour=23, minute=59, second=59) + one_day
            beginstamp = int(time.mktime(begintime.timetuple()))
            endstamp = int(time.mktime(endtime.timetuple()))
            # 转换datetime格式为字符串
            b1 = str(back_time)
            b2 = str(begintime)
            b3 = str(endtime)
            b4 = beginstamp
            b5 = endstamp
            # return [back_time, begintime, endtime, beginstamp, endstamp]  # 直接返回列表,数据都是元组datetime格式
            return [b1, b2, b3, b4, b5]
        else:
            return None
