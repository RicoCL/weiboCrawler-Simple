#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:05
# @Author  : RicoCL
# @File    : rctool.py

# 工具 存放业务无关工具方法

import requests
import random
import time
import datetime
import os
import re


# 发起请求，代理没有设置完全 表示不启用代理，json解析
def request(url, proxies={'http': [], 'https': []}):
    proxy_dict = {}

    try:
        # 随机获取代理池内ip
        http_len = len(proxies.get('http'))
        https_len = len(proxies.get('https'))
        if http_len > 0 and https_len > 0:
            http_ip_index = random.randint(0, http_len - 1)
            https_ip_index = random.randint(0, https_len - 1)
            proxy_dict['http'] = 'http://' + proxies['http'][http_ip_index]
            proxy_dict['https'] = 'https://' + proxies['https'][https_ip_index]
            print(f'\n本次请求代理ip：{proxy_dict}')
    except Exception as e:
        print(f'⚠️ - 请正确设置代理：', e)

    # 设置请求头
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'
    }

    # 请求数据
    try:
        r = requests.get(url, timeout=10, headers=headers, proxies=proxy_dict)
        # 将请求数据变成文字
        r.encoding = 'utf-8'
        json = r.json()
        # 打印出 结果
        print(json)
        return json
    except Exception as e:
        print(f'❌️ - url请求失败：{url}， ', e)
        time.sleep(0.3)  # 失败后进行重试
        print('正在重试请求。。。')
        return request(url, proxies)


# 写入文件，文件名，内容，后缀，路径
def write_to_file(file_name, content, extension='csv', file_path='../../weibo output'):
    # 如果文件名没有添加后缀，默认添加.csv
    if not str(file_name).endswith('.csv'):
        file_name = file_name + '.' + extension
    # 创建目录
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_path = os.path.join(file_path, file_name)
    # 写入文件
    with open(file_path, 'a', encoding='utf-8') as fh:
        fh.write(content + "\n")

# 时间格式统一
def time_formate(time_str):
    # 获取当前年
    current_year = time.strftime('%Y')

    # 获取当前日期
    current_date = time.strftime('%Y-%m-%d')

    # 获取昨天日期
    now_time = datetime.datetime.now()
    yes_time = now_time - datetime.timedelta(days=1)
    yes_time_date = yes_time.strftime('%Y-%m-%d')

    if '小时前' in time_str:
        h = int(time_str[0:-3])
        s = h*60*60
        time_date = now_time + datetime.timedelta(seconds=-s)
        time_str = time_date.strftime('%Y-%m-%d')
    elif '分钟前' in time_str:
        m = int(time_str[0:-3])
        s = m*60
        time_date = now_time + datetime.timedelta(seconds=-s)
        time_str = time_date.strftime('%Y-%m-%d')
    elif '秒前' in time_str:
        s = int(time_str[0:-2])
        s = s
        time_date = now_time + datetime.timedelta(seconds=-s)
        time_str = time_date.strftime('%Y-%m-%d')
    elif '刚刚' in time_str:
        time_str = current_date
    elif '昨天' in time_str:
        # 昨天微博
        time_str = yes_time_date
    elif len(time_str) < 10:
        # 当年微博
        time_str = current_year + '-' + time_str

    return time_str



def filter_tags(htmlstr):
    # 先过滤CDATA
    re_cdata = re.compile("//<!CDATA\[[>]∗//\]>", re.I)  # 匹配CDATA
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style
    re_br = re.compile('<br\s*?/?>')  # 处理换行
    re_h = re.compile('</?\w+[^>]*>')  # HTML标签
    re_comment = re.compile('<!--[^>]*-->')  # HTML注释
    s = re_cdata.sub('', htmlstr)  # 去掉CDATA
    s = re_script.sub('', s)  # 去掉SCRIPT
    s = re_style.sub('', s)  # 去掉style
    s = re_br.sub('\n', s)  # 将br转换为换行
    s = re_h.sub('', s)  # 去掉HTML 标签
    s = re_comment.sub('', s)  # 去掉HTML注释
    # 去掉多余的空行
    blank_line = re.compile('\n+')
    s = blank_line.sub('\n', s)
    s = replaceCharEntity(s)  # 替换实体
    return s


# #替换常用HTML字符实体.
# 使用正常的字符替换HTML中特殊的字符实体.
# 你可以添加新的实体字符到CHAR_ENTITIES中,处理更多HTML字符实体.
# @param htmlstr HTML字符串.
def replaceCharEntity(htmlstr):
    CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"''"', '34': '"', }
    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(htmlstr)
    while sz:
        entity = sz.group()  # entity全称，如>
        key = sz.group('name')  # 去除&;后entity,如>为gt
        try:
            htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
        except KeyError:
            # 以空串代替
            htmlstr = re_charEntity.sub('', htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
    return htmlstr

# def repalce(s, re_exp, repl_string):
#     return re_exp.sub(repl_string, s)

# test
if __name__ == "__main__":

    data = request('https://m.weibo.cn/api/container/getIndex?type=uid&value=5203786516')

    write_to_file('test', str(data))

