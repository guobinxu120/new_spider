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
    name = "untraveledplaces"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://untraveledplaces.com/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        urls = response.xpath('//ul[@class="sub-menu"]/li/a/@href').extract()
        for parent_cat in urls:
            yield Request(response.urljoin(parent_cat), self.parse1)
    def parse1(self, response):
        posts = response.xpath('//article')
        for post_tag in posts:
            item = OrderedDict()
            keys_text = post_tag.xpath('./@class').extract_first()
            texts = keys_text.split(' ')
            keywords = []
            key_temps = []
            for txt in texts:
                first_txt = txt.split('-')[0]
                if 'category' == first_txt or 'tag' == first_txt:
                    try:
                        keys = txt.split('-')
                        for i, key in enumerate(keys):
                            if i == 0: continue
                            if not key in key_temps and len(key) < 50:
                                keywords.append({'keyword': key})
                                key_temps.append(key)
                    except:
                        continue

            item['keywords'] = keywords
            item['title'] = post_tag.xpath('.//a[@rel="bookmark"]/text()').extract_first()
            item['url'] = post_tag.xpath('.//a[@rel="bookmark"]/@href').extract_first()
            contributor = ''.join(post_tag.xpath('.//a[@class="author-link"]/text()').extract()).strip()
            item['contributors'] = [{"contributor": contributor}]


            item['articleDate'] = ''
            post_time = post_tag.xpath('.//time[@class="updated hidden"]/@datetime').extract_first()
            if post_time:
                item['articleDate'] = post_time
            else:
                item['articleDate'] = post_tag.xpath('.//time[contains(@class,"entry-date published")]/@datetime').extract_first()

            # yield Request('https://motorbikewriter.com/ducati-build-300cc-bikes-india/', self.final_parse, meta={'item': item})
            yield Request(item['url'], self.final_parse, meta={'item': item})

        next_url = response.xpath('//div[@class="nav-previous"]/a/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse1)

    def final_parse(self, response):

        item = response.meta['item']
        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        if abstract:
            if 'Click title above to see video' in abstract: abstract = ''
            item['abstract'] = abstract.replace('\u00a0', '')
        else:
            item['abstract'] = ""

        tags = response.xpath('//div[@class="entry-content clearfix"]/*')
        total_text = ''
        images = []
        for tag in tags:
            tag_name = tag._root.tag
            if tag_name.lower() == 'p' or tag_name.lower() == 'figure':
                img_tags = tag.xpath('.//img')
                if img_tags:
                    for img_tag in img_tags:
                        img_url = img_tag.xpath('./@data-large-file').extract_first()
                        img_caption = img_tag.xpath('./@data-image-title').extract_first()
                        if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
                        if '.jpg?' in img_url:
                            img_url = img_url.split('.jpg?')[0]+'.jpg'
                        if '.png?' in img_url:
                            img_url = img_url.split('.png?')[0]+'.png'
                        images.append({"src": img_url.strip(), "caption": img_caption})
                else:
                    text = ''.join(tag.xpath('.//text()').extract())
                    if text == '' or 'Click title above to see video' in text: continue
                    if '___' in text: break
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
