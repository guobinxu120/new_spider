# -*- coding: utf-8 -*-

from scrapy import Spider, Request
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.?>.*?</script>', '', text)
    return text
class dasoertlicheSpider(Spider):
    name = "thechanceofchoice"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://www.thechanceofchoice.com/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    # def parse(self, response):
    #     urls = response.xpath('//div[@class="item-details"]')
    #     for parent_cat in urls:
    #         p_cat = parent_cat.xpath('./a/text()').extract_first()
    #         if not p_cat == 'Home' and not p_cat == 'Gear Shop':
    #             cat_urls = parent_cat.xpath('./ul[@class="sub-menu"]/li/a/@href').extract()
    #             for url in cat_urls:
    #                 yield Request(response.urljoin(url), self.parse1)
    def parse(self, response):
        posts = response.xpath('//div[@class="item-details"]')
        for post_tag in posts:
            item = OrderedDict()
            keys_text = post_tag.xpath('.//a[@class="td-post-category"]/text()').extract_first()
            texts = keys_text.split(',')
            keywords = []
            key_temps = []
            for txt in texts:
                if not txt.strip() in key_temps and len(txt.strip()) < 50:
                    keywords.append({'keyword': txt.strip()})
                    key_temps.append(txt.strip())

            item['keywords'] = keywords
            item['title'] = post_tag.xpath('.//a[@rel="bookmark"]/text()').extract_first()
            item['url'] = post_tag.xpath('.//a[@rel="bookmark"]/@href').extract_first()
            contributor = post_tag.xpath('.//span[@class="td-post-author-name"]/a/text()').extract_first()
            if contributor:
                item['contributors'] = [{"contributor": contributor}]
            else:
                item['contributors'] = [{"contributor": ''}]

            item['articleDate'] = ''
            post_time = post_tag.xpath('.//span[@class="td-post-date"]/time/@datetime').extract_first()
            if post_time:
                item['articleDate'] = post_time

            # yield Request('https://motorbikewriter.com/ducati-build-300cc-bikes-india/', self.final_parse, meta={'item': item})
            yield Request(item['url'], self.final_parse, meta={'item': item})

        next_url = response.xpath('//i[@class="td-icon-menu-right"]/parent::a/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse)

    def final_parse(self, response):

        item = response.meta['item']
        abstract = response.xpath('//meta[@name="description"]/@content').extract_first()
        if abstract:
            item['abstract'] = abstract
        else:
            item['abstract'] = ""

        tags = response.xpath('//div[@class="td-post-content"]/*')
        total_text = ''
        images = []
        for tag in tags:
            img_tags = tag.xpath('.//img')
            if img_tags:
                img_tags = tag.xpath('.//img[not(contains(@class,"wp-image-2413"))]')
                for img_tag in img_tags:
                    img_url = img_tag.xpath('./@data-lazy-src').extract_first()
                    if img_url == "https://www.thechanceofchoice.com/wp-content/uploads/2017/06/article-ending.png": continue
                    img_caption = img_tag.xpath('./@alt').extract_first()
                    if not img_caption:
                        img_caption = ''
                    if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
                    img_url = re.sub('-(\d+?)x(\d+?).jpg', '.jpg', img_url)
                    images.append({"src": img_url, "caption": img_caption})
            else:
                text = tag.extract()
                if text:
                    total_text += delettags(text)

        item['text'] = total_text
        item['images'] = images
        item['price'] = '5000'

        self.count += 1
        print self.count
        yield item





        # def runspider():
        #     process = CrawlerProcess({
        #         'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        #         'CONCURRENT_REQUESTS': 2,
        #         'DOWNLOAD_DELAY':1,
        #         'ROBOTSTXT_OBEY': False
        #     })
        #
        #     process.crawl(dasoertlicheSpider)
        #     process.start() #
        #     writeCsv(total_list)
        #     return total_list
        #
        # dd = runspider()
