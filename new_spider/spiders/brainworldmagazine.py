# -*- coding: utf-8 -*-

from scrapy import Spider, Request
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess


def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.*?>.*?</script>', '', text)
    return text

class dasoertlicheSpider(Spider):
    name = "brainworldmagazine"

    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://brainworldmagazine.com/category/all/page/1/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
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
                            if not key in key_temps and not 'all' in key:
                                keywords.append({'keyword': key})
                                key_temps.append(key)
                    except:
                        continue
            item['keywords'] = keywords
            item['title'] = post_tag.xpath('.//a[@title]/@title').extract_first()
            item['articleDate'] = response.xpath('.//span[@class="entry-meta-date updated"]/a/text()').extract_first()
            item['url'] = post_tag.xpath('.//a[@title]/@href').extract_first()
            # yield Request('https://motorbikewriter.com/ducati-build-300cc-bikes-india/', self.final_parse, meta={'item': item})
            yield Request(item['url'], self.final_parse, meta={'item': item})

        next_url = response.xpath('//a[@class="next page-numbers"]/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse)

    def final_parse(self, response):
        item = response.meta['item']
        item['abstract'] = ''
        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        if abstract:
            item['abstract'] = ''

        texts = response.xpath('//div[@class="entry-content clearfix"]/p')
        contributor = response.xpath('//span[@class="entry-meta-author author vcard"]/a/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]
        else:
            item['contributors'] = [{"contributor": ''}]
        total_text = ''
        images = []
        imgs = response.xpath('//div[@class="entry-content clearfix"]/p/img')
        # if mainimg_url:
        #     mainimg_url = mainimg_url.split('?w=')[0]
        #     caption = response.xpath('//article/img/@alt').extract_first()
        #     images.append({"src": mainimg_url, "caption": caption})
        # imgs = response.xpath('//div[@class="entry-content"]//img')
        for img in imgs:
            img_url = img.xpath('./@src').extract_first()
            img_caption = img.xpath('./@alt').extract_first()
            if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
            images.append({"src": img_url.strip(), "caption": img_caption})
        for i, p_tag in enumerate(texts):
            img = p_tag.xpath('./img')
            # if i == len(texts) - 1: break
            itag = p_tag.xpath('./i')
            if not img and not itag:
                text = p_tag.extract()
                if text:
                    total_text += delettags(text)

        item['text'] = total_text
        item['images'] = images
        item['price'] = '5000'
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
