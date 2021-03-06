# -*- coding: utf-8 -*-
import scrapy
from crawler.items import ArticleItem
from scrapy_redis.spiders import RedisCrawlSpider, RedisSpider


class GnnSpider(RedisCrawlSpider):
    name = 'gnn_redis'
    allowed_domains = ['gnn.gamer.com.tw']
    redis_key = 'gnn_redis:start_urls'
    item_index = 'url'
    custom_settings = {
        'MONGODB_COLLECTION': 'gnn_game2',
        'DOWNLOADER_MIDDLEWARES': {
            'crawler.middlewares.ProxyMiddleware': 1,
        }
    }

    def parse(self, response):
        articles = response.xpath("//div[@class='GN-lbox2B']")
        for article in articles:
            url = article.xpath('h1/a/@href').extract_first()
            if url:
                url = 'https:' + url
                item = ArticleItem()
                item['website'] = 'https://gnn.gamer.com.tw'
                item['title'] = article.xpath("h1/a/text()").extract_first()
                item['url'] = url
                yield scrapy.Request(url=url, callback=self.parse_item, meta={'item': item})

    def parse_item(self, response):
        item = response.meta.get('item')
        if  not response.request.meta.get('redirect_urls'):
            item['content'] = " ".join(response.xpath('string(//div[@class="GN-lbox3B"]/div)').extract())
            item['category'] = " ".join(response.xpath('//ul[@class="platform-tag"]/li/a/text()').extract())
            item['publish_time'] = response.xpath("//span[@class='GN-lbox3C']/text()").extract_first()
        else:
            print('******************************************************************************')
            print(response.url)
            item['content'] = " ".join(response.xpath('//div[@class="MSG-list8C"]/div//text()').extract())
            item['category'] = " "
            item['publish_time'] = response.xpath('//div[@class="BH-lbox MSG-list8"]/span[2]/text()').extract_first()
        yield item
