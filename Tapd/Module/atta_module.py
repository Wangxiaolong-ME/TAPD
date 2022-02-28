import logging
import sys

from AttaAPI.atta import atta_api

sys.path.append('..')


class AttaModule:
    def __init__(self, point):
        self.point = point

    def report(self):
        if not self.point:
            return None

        logging.info(" ========== Atta_Module Running .... ========== ")

        entry_id_list = self.point.keys()

        for entry_id in entry_id_list:
            # 默认字段
            bug_id = self.point[entry_id]["bug_id"]
            title = self.point[entry_id]["title"]
            url = self.point[entry_id]["url"]
            platform = self.point[entry_id]["platform"]
            first_class = self.point[entry_id]["first_class"]
            version = self.point[entry_id]["version"]
            phone_model = self.point[entry_id]["phone_model"]

            # 业务模块字段
            key_list = list(self.point[entry_id].keys())  # 键列表

            # xlog
            if "xlog_run_time" in key_list:
                xlog_time = self.point[entry_id]["xlog_run_time"]
            else:
                xlog_time = None

            # xlog_crash
            if "crash_type" in key_list:
                crash_type = self.point[entry_id]["crash_type"]
            else:
                crash_type = None

            # csv
            if "csv_run_time" in key_list:
                csv_time = self.point[entry_id]["csv_run_time"]
            else:
                csv_time = None

            # 自动流转
            if "forward" in key_list:
                forward = self.point[entry_id]["forward"]
                keyword = self.point[entry_id]["keyword"]
                second_keyword = self.point[entry_id]["second_keyword"]
            else:
                forward = None
                keyword = None
                second_keyword = None

            # Atta上报参数
            params = {
                "f1": bug_id, "f2": title, "f3": url, "f5": xlog_time,
                "f6": csv_time, "f8": crash_type, "f9": platform, "f10": first_class,
                "f11": version, "f12": phone_model, "f13": forward, "f14": keyword,
                "f15": second_keyword
            }
            atta_api(params, "user_feedback")

        logging.info(f"Total of {len(entry_id_list)} user feedback were processed this time!")
        return True
