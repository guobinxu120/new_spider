# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree

def delettags(text):
    text = re.sub('<img.*?>|<!--.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
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
    name = "bjreview"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'http://www.bjreview.com/Africa_Travel/'

    def start_requests(self):
        # proxy = "http://yongjin:Jin1234%@au.proxymesh.com:31280"
        yield Request(self.start_url, self.parse, meta={'index':1})

    def parse(self, response):
        urls = response.xpath('//a[@class="alm"]/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), self.parse1)
    def parse1(self, response):
        tags = response.xpath('//html/body/div[3]/div[1]/div/table[1]//td[@class="you20152"]/a/@href').extract()
        if not tags:
            tags = response.xpath('//a[@class="a1"]/@href').extract()
        for url in tags:
            yield Request(response.urljoin(url), self.parse_product, meta={'item': None})


    def parse_product(self, response):
        if not response.meta['item']:
            item = OrderedDict()
            keys_texts = response.xpath('//meta[@name="Keywords"]/@content').extract_first()
            keywords = []
            if keys_texts:
                keys = keys_texts.split(',')
                for key in keys:
                    if len(key) > 50: continue
                    keywords.append({'keyword': key.strip()})
            if len(keywords) > 1:
                item['keywords'] = keywords

            title = response.xpath('//td[@class="dbt-2016e"]/text()').extract_first()
            if not title:
                title = response.xpath('//td[@class="f2"]/text()').extract_first()
            item['title'] = title.strip()
            item['url'] = response.url
            contributor = response.xpath('//td[@class="zz-2016e"]/text()').extract_first()
            if not contributor:
                contributor = response.xpath('//span[contains(@style, "FF0004")]/text()').extract_first()
            if contributor:
                contributor = contributor.split('By')[-1].strip().split(',')[0].strip()
                if 'by' in contributor.lower():
                    contributor = contributor.split('by')[-1]

                item['contributors'] = contributor

            date = response.xpath('//td[@height="38"]/text()').extract_first()
            if date:
                item['articleDate'] = date.split(':')[-1].strip()


            abstract = response.xpath('//td[@class="zy-2016e"]/text()').extract_first()
            if not abstract:
                abstract = response.xpath('//td[@class="f8"]/text()').extract_first()
            if abstract:
                if len(abstract) > 1000:
                    abstract = abstract[0:1000]
                item['abstract'] = abstract


            images = []

            tags = response.xpath('//div[@class="TRS_Editor"]//p')
            total_text = ''
            if not tags:
                tags = response.xpath('//td[@style="font-size:14px;line-height:150%"]//p')
            imgs = response.xpath('//td[@style="font-size:14px;line-height:150%"]//img')
            j = 0
            for i, tag in enumerate(tags):
                image = tag.xpath('.//img')
                if image:
                    img_url = image.xpath('./@src').extract_first()
                    img_url = imagefilter(response.urljoin(img_url))
                    if not img_url or len(img_url) > 300: continue
                    img_caption = ''
                    if i < len(tags) - 1:
                        img_caption = tags[i+1].xpath('./@align').extract_first()
                        sec_images = tags[i + 1].xpath('.//img')
                        if (img_caption == "center" or img_caption == "left") and not sec_images:
                            img_caption = ''.join(tags[i + 1].xpath('.//text()').extract()).strip()
                            if len(img_caption) > 700:
                                img_caption = img_caption[0:700]
                        else:
                            img_caption = ''

                    images.append({"src": img_url, "caption": img_caption})
                else:
                    img_caption = tag.xpath('./@align').extract_first()
                    if img_caption and img_caption == "left" and imgs:
                        if j < len(imgs):
                            img_url = response.urljoin(imgs[j].xpath('./@src').extract_first())
                            img_caption = ''.join(tag.xpath('.//text()').extract()).strip()
                            images.append({"src": img_url, "caption": img_caption})
                            j += 1
                    elif img_caption != "left" and img_caption != "center":
                        text = tag.extract()
                        total_text += delettags(text)

            item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
            item['price'] = '5000'

            item['images'] = images


            next_url = response.xpath('//a[text()=Next]/@href').extract_first()
            if next_url:
                yield Request(response.urljoin(next_url), self.parse_product, meta={'item' : item})
            else:
                self.count += 1
                print self.count
                yield item
        else:
            item = response.meta['item']

            images = item['images']

            tags = response.xpath('//div[@class="TRS_Editor"]/div/p')
            total_text = item['text']
            if not tags:
                tags = response.xpath(
                    '///body/table[2]/tbody/tr/td[4]/table[2]/tbody/tr/td[1]/table[1]/tbody/tr[6]/td/p')

            for i, tag in enumerate(tags):
                image = tag.xpath('.//img')
                if image:
                    img_url = image.xpath('./@src').extract_first()
                    img_url = imagefilter(response.urljoin(img_url))
                    if img_url or len(img_url) > 300: continue
                    img_caption = tags[i + 1].xpath('./@align').extract_first()
                    sec_images = tags[i + 1].xpath('.//img')
                    if (img_caption == "center" or img_caption == "left") and not sec_images:
                        img_caption = ''.join(tags[i + 1].xpath('.//text()').extract()).strip()
                    else:
                        img_caption = ''
                    if len(img_caption) > 700:
                        img_caption = img_caption[0:700]
                    images.append({"src": img_url, "caption": img_caption})
                else:
                    text = tag.extract()
                    total_text += delettags(text)

            item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
            item['price'] = '5000'

            item['images'] = images

            next_url = response.xpath('//a[text()=Next]/@href').extract_first()
            if next_url:
                yield Request(response.urljoin(next_url), self.parse_product, meta={'item': item})
            else:
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
