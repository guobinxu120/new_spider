# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<ins.*?>.*?</ins>', '', text)
    text = re.sub('<script.*?>.*?</script>', '', text)
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
    name = "hellosydneykids"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.hellosydneykids.com.au/post-sitemap1.xml']

    def parse(self, response):
        urls = re.findall('<loc>(.*)</loc>', response.body)
        for parent_cat in urls:
            yield Request(response.urljoin(parent_cat), self.parse_product)


        # urls = response.xpath('//ul[@id="main-nav"]//ul[@class="sub-links"]/li/a/@href').extract()
        # for url in urls:
        #     yield Request(url, self.parse1)


    def parse1(self, response):
        tags = response.xpath('//article')

        for parent_cat in tags:
            item = OrderedDict()
            keys_texts = parent_cat.xpath('.//span[@class="entry-category"]/a/text()').extract()
            keywords = []
            for key in keys_texts:
                if len(key) > 50 : continue
                keywords.append({'keyword': key.strip()})

            item['keywords'] = keywords
            articl_url = parent_cat.xpath('.//h2[@class="entry-title"]/a/@href').extract_first()

            yield Request(response.urljoin(articl_url), self.parse_product, meta={'item': item})
            # yield Request('https://www.hellosydneykids.com.au/wisemans-ferry-with-kids-day-trip-weekend-away/', self.parse_product, meta={'item': item})
        next_url = response.xpath('//a[@class="next page-numbers"]/@href').extract_first()
        if next_url:
            yield Request(response.urljoin(next_url), self.parse1)
    def parse_product(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//span[@class="entry-category"]/a/text()').extract()
        keywords = []
        for key in keys_texts:
            if len(key) > 50: continue
            keywords.append({'keyword': key.strip()})

        item['keywords'] = keywords

        item['title'] = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        item['url'] = response.url
        contributor = response.xpath('//div[@class="ProductDetailsGrid prodAccordionContent"]/div/div[@class="Value"]/text()').extract_first()
        # if contributor:
        #     contributors = []
        #     for con in contributor.split(','):
        #         contributors.append({"contributor": con.strip()})
        #     item['contributors'] = contributors
        # else:
        item['contributors'] = [{"contributor": ''}]

        item['articleDate'] = response.xpath('//meta[@property="og:updated_time"]/@content').extract_first()
        if not item['articleDate']:
            item['articleDate'] = response.xpath('//meta[@property="article:published_time"]/@content').extract_first()
        if not item['articleDate']:
            return
        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract
        else:
            item['abstract'] = ""

        images = []
        image_tags = response.xpath('//div[@class="single-box clearfix entry-content"]//img')
        for img_tag in image_tags:
            img_url = img_tag.xpath('./@src').extract_first()
            img_url = imagefilter(img_url)
            if not img_url or len(img_url) > 300: continue
            img_caption = img_tag.xpath('./following-sibling::p[@class="wp-caption-text"]/@text()').extract_first()
            if not img_caption:
                img_caption = img_tag.xpath('./@alt').extract_first()
            if not img_caption:
                img_caption = ''
            if len(img_caption) > 700:
                img_caption = img_caption[0:700]
            images.append({"src": img_url, "caption": img_caption})

        tags = response.xpath('//div[@class="single-box clearfix entry-content"]/*')
        total_text = ''

        for tag in tags:
            tag_name = tag._root.tag
            imgs = tag.xpath('.//img')
            if tag_name == 'div' or imgs: continue
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
