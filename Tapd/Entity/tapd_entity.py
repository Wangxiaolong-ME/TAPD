import sys

import jsonpath

from Tapd.Util.tapd_util import TapdUtil

sys.path.append('..')


class TapdEntity:
    """ TAPD实体 """

    def __init__(self, data_bug_response):
        """
        data_bug_response: 当前处理人所有Bug字段信息
        """
        self.response = data_bug_response
        description = jsonpath.jsonpath(data_bug_response, "$.description")
        if description:
            self.des = description[0]
            self.util = TapdUtil(self.des)

    @property
    def entry_id(self):
        entry_id = jsonpath.jsonpath(self.response, "$.id")
        return entry_id[0]

    @property
    def bug_id(self):
        bug_id = self.entry_id[-8:]
        return bug_id

    @property
    def url(self):
        url = f"http://tapd.oa.com/10118351/bugtrace/bugs/view?bug_id={self.bug_id}&jump_count=1"
        return url

    @property
    def title(self):
        title = jsonpath.jsonpath(self.response, "$.title")
        return title[0]

    @property
    def first_class(self):
        first_class = jsonpath.jsonpath(self.response, "$.custom_field_two")
        return first_class[0]

    @property
    def second_class(self):
        second_class = jsonpath.jsonpath(self.response, "$.custom_field_40")
        return second_class[0]

    @property
    def back_time(self):
        back_time = self.util.back_time()
        return back_time

    @property
    def qimei(self):
        qimei = self.util.qimei()
        return qimei

    @property
    def version(self):
        version = self.util.version()
        return version

    @property
    def phone_model(self):
        phone_model = self.util.phone_model()
        return phone_model

    @property
    def platform(self):
        if self.phone_model:
            if "iPhone" not in self.phone_model or "Android" in self.second_class:
                platform = "Android"
            else:
                platform = "IOS"
        else:
            platform = "Android"
        return platform
