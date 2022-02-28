import logging
import xlwt

from Tapd.Module.tapd_module import TapdModule
from Tapd.Util.excel_util import build_bar_chart
from Tapd.Util.jieba_util import JiebaUtil
from Apollo.apollo_api import AutoForwardConfig
import numpy as np


# 获取转需类TAPD
def get_tapd():
    tapd = TapdModule().TapdInfoModule()
    first_class = ['手图重构FT驾车线', '手图重构FT公交线', '手图重构FT基础线', '手图重构FT性能线']
    ft_tapd = {}
    for ft in first_class:
        tapd_data = tapd.get_single_tapd_module(limit=200, v_status="转需求", custom_field_two=ft)  # custom_field_two
        ft_tapd[ft] = tapd_data

    return ft_tapd


# 字典排序
def sort_dict(dic):
    return dict(sorted(dic.items(), key=lambda kv: (kv[1], kv[0]), reverse=True))


# 取字典前N个数据
def top_lines(dic, top=10):
    new_dic = {}
    keys = list(dic.keys())
    for i in range(len(keys)):
        if i == top:
            break
        new_dic[keys[i]] = dic[keys[i]]  # 赋值给新字典

    return new_dic


# 字典值求和
def sum_dict(dic):
    values = list(dic.values())
    total = sum(values)
    return total


# 词频、逆文档频率计算
def frequency(dic, total, mode=1):
    """
    mode: 1:tf词频计算, 2:idf逆文档频率计算

    词频:  TAPD某词出现次数 / 总词数
    逆文档频率: log(文章总数 / 出现某词的文章数)
    """
    new_dic = {}
    # tf词频
    if mode == 1:
        for k, v in dic.items():
            if v > 0:
                fq = v / total
                if fq > 0:
                    new_dic[k] = fq

    # idf 逆文档频率
    if mode == 2:
        for k, v in dic.items():
            if v > 0:
                fq = np.log(total / v)
                if fq > 0:
                    new_dic[k] = fq

    return new_dic


# 最终词频计算
def tf_idf_frequency(tf, idf):
    tf_idf = {}
    for k, v in tf.items():
        if idf.get(k):
            tf_idf[k] = round(v * idf[k], 3)

    return tf_idf


# 主函数
def get_tf_idf(total_entity, top=20):
    ft_list = list(total_entity.keys())

    # 获取阿波罗流转配置(词典,停用词)
    forward = AutoForwardConfig.AutoForwardFTConfig()
    forward.build_config()

    total_tf_idf = {}

    for ft in ft_list:
        # 根据各自FT获取对应词典
        ft_config = forward.matching_ft_config  # 获取FT信息配置
        ft_class = list(ft_config.keys())  # {'驾车': '驾车', '公交': '公交', '基线': '基', '性能': '性能'}
        for f in ft_class:
            if str(ft).__contains__(f):
                ft_name = f
        feedback = AutoForwardConfig.FTConfig(ft_name)

        tf_dict = {}  # 词频:  TAPD某词出现次数 / 总词数
        idf_dict = {}  # 逆文档频率: 总文章数 / 出现某词的文章数

        id_list = list(total_entity[ft].keys())
        for entry_id in id_list:

            if not entry_id:
                continue

            data = total_entity[ft][entry_id]

            # 分词
            jb = JiebaUtil()
            if feedback:
                words = jb.cut_words(feedback.userdict, "stopwords.txt", data.title)
            else:
                words = jb.cut_words("user_dict.txt", "stopwords.txt", data.title)

            # 词频
            for word in words:
                if tf_dict.get(word):
                    tf_dict[word] += 1
                else:
                    tf_dict[word] = 1

            # 逆文档频率
            repeat_word = []  # 一个文章只记录一次,去重的作用
            for word in words:
                if word in repeat_word:
                    continue
                if idf_dict.get(word):
                    idf_dict[word] += 1
                    repeat_word.append(word)
                else:
                    idf_dict[word] = 1
                    repeat_word.append(word)

        total = sum_dict(tf_dict)  # 总词数
        total_tapd = len(total_entity[ft].keys())  # 总文章数

        logging.info(total, total_tapd)

        # 计算词频
        tf = frequency(tf_dict, total)
        idf = frequency(idf_dict, total_tapd, mode=2)
        tf_idf = tf_idf_frequency(tf, idf)

        tf_idf = sort_dict(tf_idf)  # 排序

        total_tf_idf[ft] = top_lines(tf_idf, top=top)    # 筛序前n行

    return total_tf_idf


# 写入Excel
def write_to_excel(dic, file_name):
    work = xlwt.Workbook(encoding="utf-8")
    ft_list = dic.keys()
    for ft in ft_list:
        sheet = work.add_sheet(ft)

        # 写入标题
        sheet.write(0, 0, label='词语')
        sheet.write(0, 1, label='词频')

        row = 1
        column = 0

        for k, v in dic[ft].items():
            sheet.write(row, column, label=k)
            sheet.write(row, column + 1, label=v)
            row += 1

    work.save(file_name)
    return file_name


def main():
    # 从阿波罗拉取公共配置
    apollo = AutoForwardConfig()
    apollo.AutoForwardPublicConfig().build_config()

    # 获取转需TAPD
    entity = get_tapd()

    # 获取词频
    tf_idf = get_tf_idf(entity, top=60)

    # 写入Excel
    excel = write_to_excel(tf_idf, "TF-IDF.xlsx")

    # 生成柱形图
    build_bar_chart(excel, "词频统计.xlsx")


if __name__ == '__main__':
    main()
