import logging
import jsonpath

from Apollo.apollo_api import load_user_feedback_config, AutoForwardConfig
from Tapd.Config import config
from Tapd.Entity.tapd_entity import TapdEntity
from Tapd.Service.tapd_service import TapdApi
from Tapd.Util.jieba_util import JiebaUtil


# 加工tapd信息
class TapdModule:
    class TapdInfoModule:

        # 获取一个TAPD请求下data下的Bug字段信息
        @staticmethod
        def get_single_tapd_data_bug(tapd_response):
            # 获取所有Bug字段信息
            data_bug_response = jsonpath.jsonpath(tapd_response, "$.data[*].Bug")
            if data_bug_response:
                return data_bug_response
            else:
                return None

        # 获取一次TAPD请求的数据,加工返回 Entity
        def get_single_tapd_module(self, **kwargs):
            """
             获取一个处理人名下TAPD信息
             current_owner: 当前处理人(一个处理人)

            """
            tapd = TapdApi()  # 实例化TAPD接口请求
            response = tapd.get_bugs(**kwargs)
            if response:

                response = response.json()  # 转json格式

                # 获取单次TAPD请求数据中的所有Bug字段
                bug_info = self.get_single_tapd_data_bug(response)
                current_owner_tapd = dict()  # 当前处理人的TAPD数据(一次请求为一个处理人)

                if bug_info:
                    # 循环对每一个Bug字段进行加工
                    for single in bug_info:
                        # 对当前这一条用反进行加工筛取需要的字段值
                        tapd_entity = TapdEntity(single)
                        current_owner_tapd[tapd_entity.entry_id] = tapd_entity

                    return current_owner_tapd
                else:
                    return None

        # 获取所有TAPD信息
        def get_total_tapd_module(self):
            total_tapd = dict()
            status = load_user_feedback_config("status_config", "status")  # 阿波罗 处理人状态
            owner_list = load_user_feedback_config("owner_config", "owner")  # 阿波罗 处理人列表
            for cu_owner in owner_list:
                logging.info(f"{cu_owner}")
                current_owner_tapd = self.get_single_tapd_module(current_owner=cu_owner, v_status=status)
                total_tapd[cu_owner] = current_owner_tapd
            return total_tapd

    class CommentModule:
        def __init__(self, entry_id):
            """
                   entry_id_data: 单条entry_id下的data集合
            """
            self.entry_id = entry_id
            self.bug_id = self.entry_id[-8:]
            self.comment_content = config.comment_text

        def get_comment(self):
            tapd = TapdApi()
            response = tapd.get_comments(entry_id=self.entry_id)
            if response:
                description = jsonpath.jsonpath(response.json(), "$.data[*].Comment.description")
                if description:
                    return description
                else:
                    return False
            else:
                return False

        # 根据评论内容判断
        def judge_by_comment(self, comment_type):
            """
            Args:
                comment_type: ["xlog", "csv", "xlog_null", "crash_key", "xcrash", "forward"]
            Returns: True:历史已评论过，False：当前为首次评论
            """
            if comment_type in ["xlog", "csv"]:
                log_text = f"was already uploaded!"
            else:
                log_text = f"comment has been added!"
            description = self.get_comment()
            if description:
                comment_text = self.comment_content[comment_type]
                if comment_text in str(description):  # 历史评论过,返回真
                    logging.info(f"bug_id: {self.bug_id},{comment_type} {log_text}")
                    return True
                else:
                    return False
            else:
                return False

        def add_comment(self, comment_type, *args):
            """
            comment_type: ["xlog", "csv", "xlog_null", "xcrash", "forward", "extend"]
            当类型为crash_key时: 需要添加额外参数 {log_name:xxx, crash_info:xxx}
            """
            tapd = TapdApi()

            content = self.comment_content[comment_type]

            if comment_type == "extend":
                content = args

            response = tapd.add_comments(description=content, entry_id=self.entry_id)

            if response:
                logging.info(f"{comment_type} comment add success!")

    class UploadModule:
        def __init__(self, entry_id):
            self.entry_id = entry_id

        def upload(self, log, log_path):
            file = {"file": (log, open(log_path, "rb"), "text/html")}
            tapd = TapdApi(files=file)
            response = tapd.upload(entry_id=self.entry_id)
            if response:
                return True
            return False

    class AutoForwardModule:
        def __init__(self, entry_id_data, forward):
            self.entry_id_data = entry_id_data
            self.entry_id = entry_id_data.entry_id
            self.title = entry_id_data.title
            self.url = entry_id_data.url
            self.class_one = self.entry_id_data.first_class
            self.class_two = self.entry_id_data.second_class
            self.jieba = JiebaUtil()
            self.comment = TapdModule.CommentModule(self.entry_id)
            self.tapd = TapdApi()
            # 初始化自动流转模块
            self.forward = forward

        # 流转操作
        def main(self):
            ft_config = self.forward.matching_ft_config  # 获取FT信息配置
            ft_class = list(ft_config.keys())  # {'驾车': '驾车', '公交': '公交', '基线': '基', '性能': '性能'}

            for ft in ft_class:
                if ft_config[ft] in self.class_one or ft_config[ft] in self.class_two:  # 匹配一二级FT
                    message, keywords = self.matching(ft)  # 分词匹配
                    return message, keywords
            return None, f"unknown ft:{self.class_one}"

        # 分词匹配
        def matching(self, _ft_class):
            # 初始化用反流转相关阿波罗配置信息
            feedback = AutoForwardConfig.FTConfig(_ft_class)
            # 对标题进行切分
            words = self.jieba.cut_words(feedback.userdict, self.forward.stopwords, self.title)  # 对标题进行切分
            t_f, keywords = self.jieba.hit_class_keyword(words, feedback.keywords,
                                                         feedback.second_keywords)  # True or False，匹配的聚类类别 or 没有匹配到
            if t_f is True:
                message = self.matching_owner(keywords, feedback.owner, _ft_class)  # 转发
                if message:
                    return message, keywords
                return False, keywords
            else:
                return False, keywords

        # 转发相关处理人
        def matching_owner(self, keywords, owner, ft):
            title = self.title
            tapd_url = self.url
            data = {"id": self.entry_id}
            describe = self.forward.describe

            # 返回的消息内容
            def message():
                # 要通知的成员
                ping = []  # ['<@zhangsan>','<@lisi>']
                for ow in owner:
                    ping.append(f"<@{ow}>")
                ping = ''.join(ping)  # '<@zhangsan><@lisi>'

                # 关键词提取
                keyword = keywords[0]
                describe_info = ''

                if keyword in describe[ft]:
                    describe_info = f"描述:{describe[ft][keyword]};"  # 关键词描述信息
                info = f"匹配关键词:{keyword},{describe_info}"

                # 匹配二级关键词时:
                if len(keywords) > 1:
                    keyword = keywords[0]
                    second_keyword = keywords[1]
                    info = f"匹配关键词:{keyword},二级关键词:{second_keyword},{describe_info}"

                # 组成消息通报群消息
                information = f"{title}\n{tapd_url}\n{info} 已流转给{ping}"
                return information

            comment = self.comment.judge_by_comment("forward")  # 获取自动流转评论
            if comment is False:  # 为首次评论
                current_owner = ';'.join(owner)  # 分号为分隔符,传入多个处理人
                self.tapd.change_owner(**data, current_owner=current_owner)  # 流转给对应处理人
                self.comment.add_comment("forward")  # 添加自动流转评论
                return message()
            else:
                return False
