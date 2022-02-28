import logging
import re
import sys

import jieba

from Tapd.Util.normal_util import read_csv_file

sys.path.append('..')


# 读取停用词文件，返回停用词列表
def read_stopwords(stop_file):
    with open(stop_file, "r", encoding='utf-8') as f:
        content = f.readlines()
        # 剔除换行符
        for i in range(len(content)):
            content[i] = content[i].replace('\n', '')
        return content


# 第一次对文本进行处理,删除用反文本中开头标题语,任意空白符、特殊符号   【【手图用户反馈新平台】用反分发-手图用反FT-北京市：】
def first_del(word):
    # 删除标题语
    title_regex = re.search(r"(【.+?市)|(【.+?--)", word)
    if title_regex:
        word = word.replace(title_regex.group(), "")

    # 删除句子中特殊符号
    marks_regex = re.findall(r"([\s\W])", word)
    if marks_regex:
        # 剔除匹配到的各种特殊符号
        word_list = [del_str for del_str in list(word) if del_str not in marks_regex]
        # 重组为句子
        word = ''.join(word_list)

    return word


# 对分词结果剔除停用词
def del_stopwords(stopword_file, word_list):
    stopword_list = read_stopwords(stopword_file)
    del_index = []
    for i in range(len(word_list)):
        if word_list[i] in stopword_list:
            del_index.append(i)
    word_list = [word for index, word in enumerate(word_list) if index not in del_index]
    return word_list


class JiebaUtil:
    @staticmethod
    def cut_words(jieba_dict, stopword_file, word):  # 将长句切分,返回列表
        # 读取词典
        jieba.load_userdict(jieba_dict)
        # 删除固定标题名
        word = first_del(word)
        # 精确模式,分割词语
        word_list = jieba.lcut(word)
        # 删除停用词
        new_word_list = del_stopwords(stopword_file, word_list)
        logging.info(f"Jieba cut words:{','.join(new_word_list)}")
        return new_word_list

    @staticmethod
    # 以切割后的词组列表去匹配 聚类词库,返回词库的column标题,既:类别
    def hit_class_keyword(word_list, keywords_csv, second_keyword_csv):
        """
        word_list: 分词后的词组列表
        keywords_csv: 关键词配置文件
        second_keyword_csv： 二级关键词文件

        return: True or False, 聚类标题
        """
        dataset, columns, index = read_csv_file(keywords_csv)  # 读取csv返回数据集，列，行
        c_dataset, c_columns, c_index = read_csv_file(second_keyword_csv)  # 读取二级关键词csv文件

        # 先从每一列遍历
        for column in columns:
            # 再遍历当前列的每一行
            for row in index:
                # 当前c列的i行关键词 是否在 词组列表中
                word = dataset[column][row]
                if type(word) is not str:  # 非字符串为空,执行下一列的循环
                    break
                for every_word in word_list:
                    if word in every_word:  # 命中关键词
                        logging.info(f"关键词:{word}")
                        if word in c_columns:
                            for c_row in c_dataset[word]:  # 遍历二级关键词
                                if c_row in word_list:
                                    logging.info(f"二级关键词:{c_row}")
                                    return True, [word, c_row]
                            else:
                                logging.info("未匹配到二级关键词")
                                break  # 跳到下一行继续循环
                        else:
                            return True, [word]
        return False, "无匹配关键词"
