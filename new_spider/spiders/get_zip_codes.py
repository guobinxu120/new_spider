# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree

def delettags(text):
    text = re.sub('<img.*?>|<!--.*?>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.*?>.*?</script>', '', text)
    text = re.sub('<ins.*?>.*?</ins>', '', text)
    text = re.sub('<iframe.*?>.*?</iframe>', '', text)
    return text

def imagefilter(text):
    if not text:
        return None
    img_url = text
    if '.jpg?' in img_url.lower():
        img_url = img_url.split('?')[0]
    elif '.png?' in img_url.lower():
        img_url = img_url.split('.png?')[0]
    elif '.jpeg?' in img_url.lower():
        img_url = img_url.split('.jpeg?')[0]
    elif '.tiff?' in img_url.lower():
        img_url = img_url.split('.tiff?')[0]
    if '.jpg' in img_url.lower() or '.jpeg' in img_url.lower() or '.png' in img_url.lower() or '.tiff' in img_url.lower():
        return img_url
    else:
        return None


class dasoertlicheSpider(Spider):
    name = "get_zip_codes"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://worldpostalcode.com/united-states/'

    def start_requests(self):
        # proxy = "http://yongjin:Jin1234%@au.proxymesh.com:31280"
        yield Request(self.start_url, self.parse, meta={'index':1})

    def parse(self, response):
        tags = response.xpath('//div[@class="regions"]/a')
        for parent_cat in tags:
            url = parent_cat.xpath('./@href').extract_first()
            state = parent_cat.xpath('./text()').extract_first()
            yield Request(response.urljoin(url), self.parse_products, meta={'state': state})

            # break


    def parse_products(self, response):
        tags = response.xpath('//div[@class="regions"]/a')
        for parent_cat in tags:
            url = parent_cat.xpath('./@href').extract_first()
            city = parent_cat.xpath('./text()').extract_first()
            if not city:
                city = parent_cat.xpath('./span/text()').extract_first()
            response.meta['city'] = city
            if city:
                yield Request(response.urljoin(url), self.parse_product, meta=response.meta)

                # break
            else:
                print('not city')

    def parse_product(self, response):
        units = response.xpath('//div[@class="units noletters"]/div/div[@class="container"]')
        for unit in units:
            title = unit.xpath('./div[1]/text()').extract_first()
            codes = unit.xpath('./div[2]/span/text()').extract()
            for code in codes:
                item = OrderedDict()
                item['state'] = response.meta['state']
                item['city'] = response.meta['city']
                item['region'] = title
                item['zipcode'] = code

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
