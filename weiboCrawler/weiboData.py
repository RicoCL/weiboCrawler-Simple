#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:12
# @Author  : RicoCL
# @File    : weiboData.py

# 对微博进行具体业务爬取


from weiboCrawler import rctool
import time
import re
import datetime

# 最大重试次数，不针对请求错误
retry_max_count = 4


# 微博类，以用户为单位
class Weibo:
    # 通过 user_id初始化，可以设置代理以及开始页数
    def __init__(self, user_id, proxy_valid=False, page_index=1, proxy_pool={}, file_path='../../weibo output', interval=0.5):
        self.file_name = user_id + "_" + datetime.datetime.now().strftime('%Y%m%d%H%M%S')  # 拼接名字成文件名
        self.file_path = file_path
        self.user_id = user_id  # 要爬取的用户id
        self.proxy_valid = proxy_valid  # 是否启用代理
        self.interval = 0.1 if proxy_valid else interval  # 每页微博爬取时间间隔
        self.page_index = page_index    # 从该页开始爬取
        self.proxy_pool = proxy_pool    # 代理ip池
        self.retry_count = retry_max_count  # 请求返回空数据后重复请求次数\
        self.profile_image_url = ''
        self.description = ''
        self.profile_url = ''
        self.verified = ''
        self.follow_count = ''
        self.screen_name = ''  # 微博昵称
        self.followers_count = ''
        self.gender = ''
        self.urank = ''
        self.weibo_containerid = ''  # 用来请求微博页时需要参数
        self.csv_headers = "微博id, 微博地址, 发布时间, 微博内容, 话题, 链接, 链接名字, 链接有效性, 点赞, 评论, 转发"
        self.weibo_arr = []  # 存放用户的微博数据

    # 获取用户基本信息
    def get_user_info(self):
        url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + self.user_id
        json = self.request(url)
        code = self.should_retry(json)
        if code == 0:
            self.get_user_info()
        elif code == -1:
            print(f"❌ - 用户 {self.user_id} 数据请求失败")
            return
        elif code == 1:
            content = json.get('data')
            self.profile_image_url = content.get('userInfo').get('profile_image_url')
            self.description = content.get('userInfo').get('description')
            self.profile_url = content.get('userInfo').get('profile_url')
            self.verified = content.get('userInfo').get('verified')
            self.follow_count = content.get('userInfo').get('follow_count')
            self.screen_name = content.get('userInfo').get('screen_name')
            self.followers_count = content.get('userInfo').get('followers_count')
            self.gender = content.get('userInfo').get('gender')
            self.urank = content.get('userInfo').get('urank')
            print(f'''
微博昵称：{self.screen_name}
微博主页地址：{self.profile_url}
微博头像地址：{self.profile_image_url}
是否认证：{str(self.verified)}
微博说明：{self.description}
关注人数：{str(self.follow_count)}
粉丝数：{str(self.followers_count)}
性别：{self.gender}
微博等级：{str(self.urank)}
            ''')
            # 顺便获取微博列表 containerid
            tabs = content.get('tabsInfo').get('tabs')
            for tab in tabs:
                if tab.get('tab_type') == 'weibo':
                    self.weibo_containerid = tab.get('containerid')

    # 分页获取微博数据
    def get_weibo_data(self):
        # 获取containerid
        if len(self.weibo_containerid) < len(self.user_id):
            self.get_user_info()
        rctool.write_to_file(self.file_name, self.csv_headers, file_path=self.file_path)
        while True:
            time.sleep(self.interval)  # 设定获取每一页的间隔时间，防止过快被封
            # 拼接出每一页的微博url
            weibo_url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + self.user_id + '&containerid=' + self.weibo_containerid + '&page=' + str(
                self.page_index)
            try:
                json = self.request(weibo_url)
                code = self.should_retry(json)
                if code == 0:
                    continue
                elif code == -1:
                    break
                elif code == 1:
                    content = json.get('data')
                    cards = content.get('cards')
                    if 0 < len(cards):
                        # 取得微博数据数组
                        for j in range(len(cards)):
                            print("--正在抓取第" + str(self.page_index) + "页，第" + str(j) + "条微博--")
                            card_type = cards[j].get('card_type')
                            if card_type == 9:
                                card = cards[j]
                                # 将微博数据转换为模型并进行处理
                                wb_model = WeiboModel(card)
                                print(wb_model.time_str)
                                # 添加微博模型到数组
                                self.weibo_arr.append(wb_model)
                                # 实时写入数据到制定文件
                                rctool.write_to_file(self.file_name, self.weibo_csv_line(wb_model), file_path=self.file_path)
                        # 处理完当业数据，准备下一页
                        self.page_index += 1
                    else:
                        break
            except Exception as e:
                print(e)

        pass

    # 生成一条数据的csv
    def weibo_csv_line(self, wb_model):
        # 格式化一条微博的一行CSV数据, 一定要与表头对应
        # "微博id, 微博地址, 发布时间, 微博内容, 话题, 链接, 链接名字, 链接有效性, 点赞, 评论, 转发"
        csv_line = (
                str(wb_model.weibo_id) + ', ' +
                wb_model.scheme + ', ' +
                wb_model.time_str + ', ' +
                wb_model.text_str + ', ' +
                wb_model.topics_str + ', ' +
                wb_model.link_url_str + ', ' +
                wb_model.link_name_str + ', ' +
                wb_model.links_valid + ', ' +
                str(wb_model.attitudes_count) + ', ' +
                str(wb_model.comments_count) + ', ' +
                str(wb_model.reposts_count))
        return csv_line

    # 批量将数据统一写入csv
    def write_to_csv(self):
        if len(self.weibo_arr) > 0:
            rctool.write_to_file(self.file_name, self.csv_headers)
            for wb_model in self.weibo_arr:
                csv_line = Weibo.weibo_csv_line(wb_model)
                rctool.write_to_file(self.file_name, csv_line)

    # 网络请求
    def request(self, url):
        if self.proxy_valid:
            return rctool.request(url, proxies=self.proxy_pool)
        else:
            return rctool.request(url)

    # 是否进行重试，返回值0 重试，返回值1，正常获取数据，返回值-1，
    def should_retry(self, json):
        sleep_time = 5
        code = json['ok']
        if code == 0:  # 无数据，10秒后重试
            self.retry_count -= 1
            if self.retry_count < 0:
                # 暂无更多重试机会
                print('❗️❗️❗️❗️重试结束，无更多数据')
                self.retry_count = retry_max_count
                return -1
            print(f'🔃 暂无数据 {str(sleep_time)} 秒后重试')
            time.sleep(sleep_time)
            return 0
        elif code == 1:
            self.retry_count = retry_max_count
            return 1
        else:
            return 1

    # 运行爬虫
    def start(self):
        try:
            self.get_weibo_data()  # 已开启实时保存
            # self.write_to_csv()
        except Exception as e:
            print('Error: ', e)


# 每条微博的数据的模型
class WeiboModel:
    def __init__(self, card):
        self.card_dict = card
        self.weibo_id = ''
        self.scheme = ''
        self.time_str = ''
        self.text_str = ''
        self.topics_str = ''
        self.link_url_str = ''
        self.link_name_str = ''
        self.links_valid = ''  # 特殊需求
        self.attitudes_count = ''
        self.comments_count = ''
        self.reposts_count = ''
        self.links = None  # 内容中提取的链接数组
        self.archive_from(card)  # 通过card字典初始化模型

    # 处理正文所带的多条链接
    def links_filter(self):
        if self.links:
            links = self.links
            link_url_str = str(len(links)) + '， '
            link_name_str = str(len(links)) + '， '
            # 遍历获取链接
            for link in links:
                link_url = link[1]  # 长的链接
                link_name = link[2]  # 链接名称
                valid = link[3]  # 链接有效性
                link_url_str = link_url_str + link_url + '， '  # 将链接拼接起来
                link_name_str = link_name_str + link_name + '， '  # 将链接的名称拼接起来

                if self.links_valid == 'yes':
                    # 有一个有效连接，标记此条微博引导链接有效
                    break
                else:
                    self.links_valid = valid
            self.link_name_str = link_name_str
            self.link_url_str = link_url_str

    # 从原始字典字典提取到模型
    def archive_from(self, card_dict):
        mblog = card_dict.get('mblog')
        weibo_id = mblog["id"]
        attitudes_count = mblog.get('attitudes_count')
        comments_count = mblog.get('comments_count')
        created_at = mblog.get('created_at')  # 微博时间
        time_str = rctool.time_formate(created_at)  # 处理微博时间
        reposts_count = mblog.get('reposts_count')
        scheme = card_dict.get('scheme')
        text = mblog.get('text')  # 原始微博内容，带HTML标签
        # 处理微博内容，返回一个元组的数组
        text_dict = filter_weibo_text(text)  # 处理微博的内容
        text_str = text_dict["text"]  # 去标签内容
        # 话题
        topics_str = ''
        if text_dict['topics']:
            topics = text_dict['topics']
            topics_str = "， ".join(topics)

        self.links = text_dict.get('links')
        self.links_filter()  # 处理正文中链接

        # 赋值
        self.weibo_id = weibo_id
        self.scheme = scheme
        self.time_str = time_str
        self.text_str = text_str
        self.topics_str = topics_str
        self.attitudes_count = attitudes_count
        self.comments_count = comments_count
        self.reposts_count = reposts_count

# 业务弱相关方法
# 微博内容过滤
def filter_weibo_text(content):

    # 准备提取话题 <span class="surl-text">#话题#</span></a>
    p_topic = r'<span class="surl-text">(#.+?#)</span></a>'
    topics = re.findall(p_topic, content)

    # 准备提取链接 <a data-url="http://t.cn/xxx短链地址xxxxx" xxxxx href="xxxxxx长链接地址xxxxxxx"xxxxxxx>xxxxxx修饰图标xxxxxx<span class="surl-text">xxxxxxx链接名字xxxxxxxx</span></a>
    p_link = r'<a data-url="(http://t.cn/.+?)".*?href="(.+?)".*?>.*?</span>.*?<span class="surl-text">(.*?)</span></a>'
    links = re.findall(p_link, content)   # 元组，短链，长链，链接名字

    # 过滤无效链接，
    links = filter_weibo_link(links)

    s = rctool.filter_tags(content)  # 移除HTML标签
    # s = s.replace('\'', '"')#
    s = s.replace(',', '，')  # 将英文逗号,分隔符转为中文逗号，
    s = s.replace('\n', ' ')  # 去掉换行
    return {'text': s, 'links': links, 'topics': topics}


# 过滤不需要的链接，links为  元组数组，（短链，长链，链接名字）在元组内添加一个字段
def filter_weibo_link(links):

    newlinks = []
    for link in links:
        valid = 'no'
        link_url = str(link[1])
        # 黑名单
        if link_url.startswith(('http://e.weibo.com/',
                                'http://event.weibo.com/',
                                'http://photo.weibo.com/',
                                'http://mission.tv.weibo.cn/')):
            valid = 'no'
        # 白名单
        elif (link_url.startswith('http://miaopai.com/show/')
              or (link_url.startswith('https://weibo.cn/') and ('http%3A%2F%2Fac.qq.com%2F' in link_url))):
            valid = 'yes'
        else:
            valid = 'unknown'

        newlinks.append(link + (valid,))

    return newlinks
