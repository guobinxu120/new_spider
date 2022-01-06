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
    name = "motorbikewriter"

    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://motorbikewriter.com'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        cats = response.xpath('//ul[@id="primary-menu"]/li')
        for parent_cat in cats:
            p_cat = parent_cat.xpath('./a/text()').extract_first()
            if not p_cat == 'Home' and not p_cat == 'Gear Shop':
                cat_urls = parent_cat.xpath('./ul[@class="sub-menu"]/li/a/@href').extract()
                if cat_urls:
                    pass
                    # for url in cat_urls:
                    #     yield Request(response.urljoin(url), self.parse1)
                else:
                    url = parent_cat.xpath('./a/@href').extract_first()
                    yield Request(response.urljoin(url), self.parse1)
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
            # yield Request('https://motorbikewriter.com/ducati-build-300cc-bikes-india/', self.final_parse, meta={'item': item})
            yield Request(item['url'], self.final_parse, meta={'item': item})

        next_url = response.xpath('//div[@class="nav-previous"]/a/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse1)

    def final_parse(self, response):
        flag_str = response.xpath('//meta[@property="article:section"]/@content').extract_first()
        if flag_str:
            if not flag_str.lower() == "motorbike news" and not flag_str.lower() == "motorbike":
                item = response.meta['item']
                # item['url'] = response.url
                item['articleDate'] = response.xpath('//div[@class="entry-meta"]//time/@datetime').extract_first()
                abstract = response.xpath('//meta[@name="description"]/@content').extract_first()
                if abstract:
                    item['abstract'] = abstract
                else:
                    item['abstract'] = ""
                texts = response.xpath('//div[@class="entry-content"]/p')
                contributor = response.xpath('//span[@class="author vcard"]/a/text()').extract_first()

                item['contributors'] = [{"contributor": contributor}]
                total_text = ''
                images = []
                mainimg_url = response.xpath('//article/img/@src').extract_first()
                if mainimg_url:
                    mainimg_url = mainimg_url.split('?w=')[0]
                    mainimg_url = mainimg_url.replace('-45x45.jpg', '.jpg')

                    if len(mainimg_url) < 300 and '.gif' in mainimg_url:
                        caption = response.xpath('//article/img/@alt').extract_first()
                        if caption and len(caption) >  700:
                            caption = caption[0:700]
                        images.append({"src": mainimg_url, "caption": caption})
                imgs = response.xpath('//div[@class="entry-content"]//img')
                for img in imgs:
                    img_url = img.xpath('./@src').extract_first()
                    img_caption = img.xpath('./following-sibling::figcaption/text()').extract_first()
                    if not img_caption:
                        img_caption = img.xpath('./@alt').extract_first()
                    if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
                    img_url = img_url.split('?w=')[0]
                    img_url = img_url.replace('-45x45.jpg', '.jpg')
                    if img_caption and len(img_caption) > 700:
                        img_caption = img_caption[0:700]
                    images.append({"src": img_url, "caption": img_caption})
                for i, p_tag in enumerate(texts):
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
