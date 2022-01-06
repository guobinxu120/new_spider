# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
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
    name = "ultimatetravelmagazine"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://www.ultimatetravelmagazine.com/'

    def start_requests(self):
        # proxy = "http://yongjin:Jin1234%@au.proxymesh.com:31280"
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        tags = response.xpath('//div[@class="SideCategoryListFlyout"]/ul/li')
        for parent_cat in tags:
            category_texts = parent_cat.xpath('./ul/li/a/@href').extract()
            if category_texts:
                for cat_url in category_texts:
                    yield Request(response.urljoin(cat_url), self.parse_products)
            else:
                cat_url = parent_cat.xpath('./a/@href').extract_first()
                yield Request(response.urljoin(cat_url), self.parse_products)


    def parse_products(self, response):
        urls = response.xpath('//ul[@class="ProductList "]/li/div/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), self.parse_product)
        next_url = response.xpath('//a[@class="nav-next"]/@href').extract_first()
        if next_url:
            yield Request(response.urljoin(next_url), self.parse_products)

    def parse_product(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//meta[@name="keywords"]/@content').extract_first()
        keywords = []
        if keys_texts:
            keys = keys_texts.split(',')
            for key in keys:
                if len(key) > 50: continue
                keywords.append({'keyword': key.strip()})

        item['keywords'] = keywords
        item['title'] = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        item['url'] = response.url
        contributor = response.xpath('//div[@class="ProductDetailsGrid prodAccordionContent"]/div/div[@class="Value"]/text()').extract_first()
        if contributor:
            contributors = []
            for con in contributor.split(','):
                contributors.append({"contributor": con.strip()})
            item['contributors'] = contributors
        else:
            item['contributors'] = [{"contributor": ''}]

        item['articleDate'] = ''

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract
        else:
            item['abstract'] = ""

        images = []
        image_tags = response.xpath('//div[@class="TinyOuterDiv"]/div/a')
        for img_tag in image_tags:
            img_text = img_tag.xpath('./@rel').extract_first()
            if img_text:
                img_url = json.loads(img_text)['largeimage']
                img_url = imagefilter(img_url)
                if not img_url or len(img_url) > 300: continue
                img_caption = img_tag.xpath('./img/@title').extract_first()
                if not img_caption:
                    img_caption = ''
                if len(img_caption) > 700:
                    img_caption = img_caption[0:700]
                images.append({"src": img_url, "caption": img_caption})

        tags = response.xpath('//div[@class="ProductDescriptionContainer prodAccordionContent"]/*')
        total_text = ''

        for tag in tags:
            text = tag.extract()
            total_text += delettags(text)

        item['text'] = total_text
        item['price'] = '5000'

        item['images'] = images

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
