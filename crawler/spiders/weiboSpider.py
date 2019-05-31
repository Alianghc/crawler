#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import codecs
import csv
import json
import os
import random
import re
from importlib import reload
import requests
import sys
import traceback
from datetime import datetime
from datetime import timedelta
from lxml import etree
from time import sleep
from tqdm import tqdm


class WeiboSpider:
    def __init__(self, user_id, filter=0):
        """Weibo类初始化"""
        try:
            with open('cookie.json') as f:
                self.cookie = json.loads(f.read())
        except:
            self.cookie = ''

        self.user_id = user_id  # 用户id，即需要我们输入的数字，如昵称为“Dear-迪丽热巴”的id为1669879400
        self.filter = filter  # 取值范围为0、1，程序默认值为0，代表要爬取用户的全部微博，1代表只爬取用户的原创微博
        self.nickname = ''  # 用户昵称，如“Dear-迪丽热巴”
        self.weibo_num = 0  # 用户全部微博数
        self.got_num = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibo = []
        # self.weibo_content = []  # 微博内容
        # self.weibo_place = []  # 微博位置
        # self.publish_time = []  # 微博发布时间
        # self.up_num = []  # 微博对应的点赞数
        # self.retweet_num = []  # 微博对应的转发数
        # self.comment_num = []  # 微博对应的评论数
        # self.publish_tool = []  # 微博发布工具

    def deal_html(self, url):
        """处理html"""
        try:
            html = requests.get(url, cookies=self.cookie).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def deal_garbled(self, info):
        """处理乱码"""
        try:
            info = info.xpath(
                "string(.)").replace(u"\u200b", "").encode(sys.stdout.encoding, "ignore").decode(
                sys.stdout.encoding)
            return info
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_nickname(self):
        """获取用户昵称"""
        try:
            url = "https://weibo.cn/%d/info" % (self.user_id)
            selector = self.deal_html(url)
            nickname = selector.xpath("//title/text()")[0]
            self.nickname = nickname[:-3]
            if self.nickname == u"登录 - 新":
                sys.exit(u"cookie错误或已过期,请按照README中方法重新获取")
            print(u"用户昵称: " + self.nickname)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_user_info(self, selector):
        """获取用户昵称、微博数、关注数、粉丝数"""
        try:
            self.get_nickname()  # 获取用户昵称
            user_info = selector.xpath("//div[@class='tip2']/*/text()")

            self.weibo_num = int(user_info[0][3:-1])
            print(u"微博数: " + str(self.weibo_num))

            self.following = int(user_info[1][3:-1])
            print(u"关注数: " + str(self.following))

            self.followers = int(user_info[2][3:-1])
            print(u"粉丝数: " + str(self.followers))
            print("*" * 100)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_page_num(self, selector):
        """获取微博总页数"""
        try:
            if selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(selector.xpath(
                    "//input[@name='mp']")[0].attrib["value"])
            return page_num
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_long_weibo(self, weibo_link):
        """获取长原创微博"""
        try:
            selector = self.deal_html(weibo_link)
            info = selector.xpath("//div[@class='c']")[1]
            wb_content = self.deal_garbled(info)
            wb_time = info.xpath("//span[@class='ct']/text()")[0]
            wb_content = wb_content[wb_content.find(
                ":") + 1:wb_content.rfind(wb_time)]
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_original_weibo(self, info):
        """获取原创微博"""
        try:
            weibo_content = self.deal_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind(u"赞")]
            a_text = info.xpath("div//a/text()")
            if u"全文" in a_text:
                weibo_id = info.xpath("@id")[0][2:]
                weibo_link = "https://weibo.cn/comment/" + weibo_id
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            wb_content = wb_content[:wb_content.rfind(u"原文转发")]
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_retweet(self, info):
        """获取转发微博"""
        try:
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if not original_user:
                wb_content = u"转发微博已被删除"
                return wb_content
            else:
                original_user = original_user[0]
            wb_content = self.deal_garbled(info)
            wb_content = wb_content[wb_content.find(
                ":") + 1:wb_content.rfind(u"赞")]
            wb_content = wb_content[:wb_content.rfind(u"赞")]
            a_text = info.xpath("div//a/text()")
            if u"全文" in a_text:
                weibo_id = info.xpath("@id")[0][2:]
                weibo_link = "https://weibo.cn/comment/" + weibo_id
                wb_content = self.get_long_retweet(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            retweet_reason = self.deal_garbled(info.xpath("div")[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex(u"赞")]
            wb_content = (retweet_reason + "\n" + u"原始用户: " +
                          original_user + "\n" + u"转发内容: " + wb_content)
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_content(self, info):
        """获取微博内容"""
        try:
            is_retweet = info.xpath("div/span[@class='cmt']")
            if is_retweet:
                weibo_content = self.get_retweet(info)
            else:
                weibo_content = self.get_original_weibo(info)
            self.weibo[-1]['weibo_content'] = weibo_content
            print(weibo_content)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_place(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath("div")[0]
            a_list = div_first.xpath("a")
            weibo_place = u"无"
            for a in a_list:
                if ("place.weibo.com" in a.xpath("@href")[0] and
                        a.xpath("text()")[0] == u"显示地图"):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        weibo_place = weibo_a[-1]
                        if u"视频" == div_first.xpath("span[@class='ctt']/a/text()")[-1][-2:]:
                            if len(weibo_a) >= 2:
                                weibo_place = weibo_a[-2]
                            else:
                                weibo_place = u"无"
                        weibo_place = self.deal_garbled(weibo_place)
                        break
            self.weibo[-1]['weibo_place'] = weibo_place
            print(u"微博位置: " + weibo_place)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            publish_time = str_time.split(u'来自')[0]
            if u"刚刚" in publish_time:
                publish_time = datetime.now().strftime(
                    '%Y-%m-%d %H:%M')
            elif u"分钟" in publish_time:
                minute = publish_time[:publish_time.find(u"分钟")]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() - minute).strftime(
                    "%Y-%m-%d %H:%M")
            elif u"今天" in publish_time:
                today = datetime.now().strftime("%Y-%m-%d")
                time = publish_time[3:]
                publish_time = today + " " + time
            elif u"月" in publish_time:
                year = datetime.now().strftime("%Y")
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = (year + "-" + month + "-" + day + " " + time)
            else:
                publish_time = publish_time[:16]
            self.weibo[-1]['publish_time'] = publish_time
            print(u"微博发布时间: " + publish_time)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split(u'来自')) > 1:
                publish_tool = str_time.split(u'来自')[1]
            else:
                publish_tool = u"无"
            self.weibo[-1]['publish_tool'] = publish_tool
            print(u"微博发布工具: " + publish_tool)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_footer(self, info):
        """获取微博点赞数、转发数、评论数"""
        try:
            pattern = r"\d+"
            str_footer = info.xpath("div")[-1]
            str_footer = self.deal_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind(u'赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            self.weibo[-1]['up_num'] = up_num
            print(u"点赞数: " + str(up_num))

            retweet_num = int(weibo_footer[1])
            self.weibo[-1]['retweet_num'] = retweet_num
            print(u"转发数: " + str(retweet_num))

            comment_num = int(weibo_footer[2])
            self.weibo[-1]['comment_num'] = comment_num
            print(u"评论数: " + str(comment_num))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        try:
            url = "https://weibo.cn/u/%d?page=%d" % (self.user_id, page)
            selector = self.deal_html(url)
            info = selector.xpath("//div[@class='c']")
            is_empty = info[0].xpath("div/span[@class='ctt']")
            if is_empty:
                for i in range(0, len(info) - 2):
                    is_retweet = info[i].xpath("div/span[@class='cmt']")
                    self.weibo.append({})
                    if (not self.filter) or (not is_retweet):
                        self.get_weibo_content(info[i])  # 微博内容
                        self.get_weibo_place(info[i])  # 微博位置
                        self.get_publish_time(info[i])  # 微博发布时间
                        self.get_publish_tool(info[i])  # 微博发布工具
                        self.get_weibo_footer(info[i])  # 微博点赞数、转发数、评论数
                        self.got_num += 1
                        print("-" * 100)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_info(self):
        """获取微博信息"""
        try:
            url = "https://weibo.cn/u/%d" % (self.user_id)
            selector = self.deal_html(url)
            self.get_user_info(selector)  # 获取用户昵称、微博数、关注数、粉丝数
            page_num = self.get_page_num(selector)  # 获取微博总页数
            page1 = 0
            random_pages = random.randint(1, 5)
            for page in tqdm(range(1, page_num + 1), desc=u"进度"):
                self.get_one_page(page)  # 获取第page页的全部微博

                # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                if page - page1 == random_pages:
                    sleep(random.randint(6, 10))
                    page1 = page
                    random_pages = random.randint(1, 5)

            if not self.filter:
                print(u"共爬取" + str(self.got_num) + u"条微博")
            else:
                print(u"共爬取" + str(self.got_num) + u"条原创微博")
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_filepath(self, type):
        """获取结果文件路径"""
        try:
            file_dir = os.path.split(os.path.realpath(__file__))[
                0] + os.sep + "weibo"
            if not os.path.isdir(file_dir):
                os.mkdir(file_dir)
            file_path = file_dir + os.sep + "%d" % self.user_id + "." + type
            return file_path
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def start(self):
        """运行爬虫"""
        try:
            self.get_weibo_info()
            print(u"信息抓取完毕")
            print("*" * 100)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()


def main():
    try:
        # 使用实例,输入一个用户id，所有信息都会存储在wb实例中
        user_id = 1669879400  # 可以改成任意合法的用户id（爬虫的微博id除外）
        filter = 1  # 值为0表示爬取全部微博（原创微博+转发微博），值为1表示只爬取原创微博
        wb = WeiboSpider(user_id, filter)  # 调用Weibo类，创建微博实例wb
        wb.start()  # 爬取微博信息
        print(u"用户昵称: " + wb.nickname)
        print(u"全部微博数: " + str(wb.weibo_num))
        print(u"关注数: " + str(wb.following))
        print(u"粉丝数: " + str(wb.followers))
        if wb.weibo:
            print(u"最新/置顶 微博为: " + wb.weibo[0]['weibo_content'])
            print(u"最新/置顶 微博位置: " + wb.weibo[0]['weibo_place'])
            print(u"最新/置顶 微博发布时间: " + wb.weibo[0]['publish_time'])
            print(u"最新/置顶 微博获得赞数: " + str(wb.weibo[0]['up_num']))
            print(u"最新/置顶 微博获得转发数: " + str(wb.weibo[0]['retweet_num']))
            print(u"最新/置顶 微博获得评论数: " + str(wb.weibo[0]['comment_num']))
            print(u"最新/置顶 微博发布工具: " + wb.weibo[0]['publish_tool'])
    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
