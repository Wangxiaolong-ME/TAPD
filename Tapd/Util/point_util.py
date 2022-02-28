import sys

sys.path.append('..')


class MergeDict:
    @staticmethod
    def max_min(dic1, dic2):
        # 取长度最大的为参照
        if len(dic1.keys()) > len(dic2.keys()):
            max_dic = dic1
            min_dic = dic2
        else:
            max_dic = dic2
            min_dic = dic1

        return max_dic, min_dic

    def get_same_key_value(self, dic1, dic2):
        max_dic, min_dic = self.max_min(dic1, dic2)

        same_key = []   # 键相同

        for k, v in max_dic.items():
            if min_dic.get(k):  # min_dic有重复键时
                same_key.append(k)

        return same_key

    def merge_dict(self, dic1, dic2):
        # 若有空值,直接返回另一个字典
        if not dic1:
            return dic2
        elif not dic2:
            return dic1

        max_dic, min_dic = self.max_min(dic1, dic2)

        same_key = self.get_same_key_value(max_dic, min_dic)    # 获取相同键(同一entry_id)

        # 相同ID下的键合并,并删除
        for key in same_key:
            max_dic[key].update(min_dic[key])
            del min_dic[key]

        # 剩下不同ID的键值对,合并
        max_dic.update(min_dic)
        return max_dic

    def merge_point(self, point_list):
        # 得到列表索引
        index = list(range(len(point_list)))  # [0,1,2]
        point = {}
        for i in index:
            point = self.merge_dict(point, point_list[i])
        return point
