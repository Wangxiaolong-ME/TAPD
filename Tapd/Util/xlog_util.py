import logging
import os
import zipfile

import jsonpath

from Tapd.Util.normal_util import reg_time, format_date


def get_file_url(json_response):
    """ 获取查询xlog接口响应信息中的fileUrl,后续下载所需的入参 """

    file_url = jsonpath.jsonpath(json_response, "$.logs[0].fileUrl")  # [0]代表最近时间的日志
    if file_url:
        return file_url
    else:
        return False


def save_data_to_file(html, file_path, mode='wb'):
    """
    保存字符串到指定文件
    Args:
        html:       str   字符串数据
        file_path:  str   文件路径
        mode:       str   文件打开格式，[w,r,a...]
    """

    # 文件目录
    file_path_dir = os.path.dirname(file_path)
    # 判断目录是否存在
    if not os.path.exists(file_path_dir):
        # 目录不存在创建，makedirs可以创建多级目录
        os.makedirs(file_path_dir)
    try:
        # 保存数据到文件
        with open(file_path, mode) as f:
            f.write(html)
        return True, '保存成功'
    except Exception as e:
        return False, '保存失败:{}'.format(e)


def unzip_file(zip_src, dst_dir):
    """

    :param zip_src: 要解压的文件绝对路径 例：d:/test/123.txt
    :param dst_dir: 解压到的目的目录
    :return:
    """
    try:
        # 下载的日志文件如果为0字节,返回False
        xlog_zip_size = os.path.getsize(zip_src)
        if xlog_zip_size:
            r = zipfile.is_zipfile(zip_src)
            if r:
                fz = zipfile.ZipFile(zip_src, 'r')
                for file in fz.namelist():
                    fz.extract(file, dst_dir)
                fz.close()
                return True
            else:
                logging.info('This is not zip')
                return False
        else:
            logging.warning(f"xlog文件大小为0字节!")
            return False
    except Exception as e:
        logging.error(f"解压文件失败！报错信息：\n{e}")
        return False


def get_xlog_endswith_date(log_files):
    """ log_files: com.tencent.sosomap_20220102.xlog ---> {'com.tencent.sosomap_20220102.xlog':'20220102'} """
    xlog_dict = {}
    for xlog in log_files:
        if xlog.endswith("xlog"):
            xlog_dict[xlog] = reg_time(xlog)  # {'com.tencent.sosomap_20220102.xlog':'20220102'}
    return xlog_dict


def get_last_two_days_xlog(xlog_dict, last_few_date):
    """
    xlog_dict: {'xxx_20220102.xlog':'20220102'}
    last_few_date: 反馈时间最近几天,2022-01-01

    return: ['xxx_20220102.xlog',''xxx_20220103.xlog'']
    """
    xlog_keys = list(xlog_dict.keys())
    for xlog in xlog_keys[::-1]:
        datetime_str = format_date(xlog_dict[xlog])
        # 2天之前的xlog删除,不解析、上传
        if datetime_str < last_few_date:
            del xlog_dict[xlog]
    return list(xlog_dict.keys())


# 读取文件前n行内容
def read_lines(file_path, line_number=40):
    """
    file_path: 文件路径
    line_number: 取文件前n行,默认40行

    return: html_txt: 评论文本;
    """
    file_name = file_path.split('/')[-1]
    all_line = open(file_path, "r", encoding='UTF-8').readlines()
    # 取前n行内容
    lines = all_line[0:line_number + 1]
    # 头部添加html元素
    lines.insert(0, '<div>\n<pre style="background-color: #2b2b2b; color: #a9b7c6;">')
    # 尾部添加html元素
    lines.append('</pre></div>')
    # 列表转字符串,行之间替换html标识符<br />
    line = '<br />'.join(lines)
    # 去多余换行
    html_txt = line.replace('\n', '')
    return html_txt
