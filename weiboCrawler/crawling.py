#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 14:55
# @Author  : RicoCL
# @File    : crawling.py

# 主要运行文件 包含配置
from weiboCrawler import weiboData

# 配置-根据自己需要进行修改
# 需要爬取的用户的微博id https://weibo.com/u/5203786516?refer_flag=1001030101_
uid = '2305872235'

# 从第几页开始爬取
page_index = 1

# 代理启用开关
proxy_valid = False

# 设置代理ip池 可去http://www.xicidaili.com找，对应http 和 https
proxy_pool = {
    'http': [
        '61.135.217.7:80',
        '118.190.95.35:9001',
    ],

    'https': [
        '124.42.68.152:90',
        '140.250.180.229:61234',
        '183.30.197.24:9797',
        '114.215.95.188:3128',
        '171.39.2.36:8123',
        '123.9.145.139:8118',
        '118.190.145.138:9001',
        '27.184.127.65:8118',
    ]
}

# 数据默认保存目录
file_path = '../../weibo output'

# 抓取时间间隔，最好不要低于0.5，防止被封
interval = 1


# 爬虫入口
def main():

    # 创建 weiboData 实例
    wb = weiboData.Weibo(uid, proxy_valid=proxy_valid, page_index=page_index, proxy_pool=proxy_pool, file_path=file_path, interval=interval)
    # 开始爬取
    wb.start()


# 程序入口
if __name__ == "__main__":
    main()

