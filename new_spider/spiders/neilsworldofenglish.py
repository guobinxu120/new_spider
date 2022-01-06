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
    name = "neilsworldofenglish"

    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://neilsworldofenglish.wordpress.com/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        posts = response.xpath('//div[@class="post-container"]')
        for post_tag in posts:
            item = OrderedDict()
            keys_text = post_tag.xpath('./div/@class').extract_first()
            texts = keys_text.split(' ')
            keywords = []
            for txt in texts:
                first_txt = txt.split('-')[0]
                if 'category' == first_txt or 'tag' == first_txt:
                    try:
                        keywords.append({'keyword': txt.split('-')[1]})
                    except:
                        continue
            item['keywords'] = keywords
            item['title'] = post_tag.xpath('.//a[@rel="bookmark"]/text()').extract_first()
            item['articleDate'] = post_tag.xpath('.//time[@class="updated"]/@datetime').extract_first()
            item['abstract'] = post_tag.xpath('.//div[@class="post-content clear"]/p/text()').extract_first()
            item['url'] = post_tag.xpath('.//h2[@class="post-title entry-title"]/a/@href').extract_first()
            yield Request(item['url'], self.final_parse, meta={'item': item})

    def final_parse(self, response):
        item = response.meta['item']
        item['url'] = response.url
        texts = response.xpath('//div[@class="post-content clear"]/p')
        contributor = texts[-1].xpath('./text()').extract_first()[1:-1].strip()

        item['contributors'] =  [{"contributor": contributor.split('and')[0]}]
        total_text = ''
        images = []
        mainimg_url = response.xpath('//div[@class="featured-media"]/img/@data-orig-file').extract_first()
        if mainimg_url:
            mainimg_url = mainimg_url.split('?w=')[0]
            meta_image = response.xpath('//div[@class="featured-media"]/img/@data-image-meta').extract_first()
            json_imgdata = json.loads(meta_image)
            caption = json_imgdata['caption']
            images.append({"src": mainimg_url, "caption": caption})

        for i, p_tag in enumerate(texts):
            img = p_tag.xpath('./img')
            if i == len(texts) - 1: break
            if not img:
                total_text += delettags(p_tag.extract())
            else:
                image_url = img.xpath('./@data-orig-file').extract_first().split('?w=')[0]
                meta_image = img.xpath('./@data-image-meta').extract_first()
                json_imgdata = json.loads(meta_image)
                caption = json_imgdata['caption']
                images.append({"src": image_url, "caption": caption})
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
