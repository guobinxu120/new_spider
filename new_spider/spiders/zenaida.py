# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.?>.*?</script>', '', text)
    return text
class dasoertlicheSpider(Spider):
    name = "zenaida"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'http://zenaida.travel/post-sitemap.xml'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        urls = re.findall('<loc>(.*)</loc>', response.body)
        for parent_cat in urls:
            yield Request(response.urljoin(parent_cat), self.parse1)
            # yield Request('http://zenaida.travel/2018/02/berlin-gianni-versace-retrospective-show/', self.parse1)
    def parse1(self, response):

        item = OrderedDict()
        keys_texts = response.xpath('//meta[@property ="article:tag"]/@content').extract()
        keywords = []
        key_temps = []
        for txt in keys_texts:
            keys = txt.split('|')
            for i, key in enumerate(keys):
                if not key.strip() in key_temps and len(key) < 50:
                    keywords.append({'keyword': key.strip()})
                    key_temps.append(key.strip())

        if not keys_texts: return

        item['keywords'] = keywords
        item['title'] = response.xpath('//h2[@class="entry-title"]/text()').extract_first()
        item['url'] = response.url
        # contributor = ''.join(post_tag.xpath('.//a[@class="author-link"]/text()').extract()).strip()
        item['contributors'] = [{"contributor": ''}]

        item['articleDate'] = response.xpath('//meta[@property ="og:updated_time"]/@content').extract_first()
        if not item['articleDate']:
            item['articleDate'] = response.xpath('//meta[@property ="article:published_time"]/@content').extract_first()

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        if abstract:
            item['abstract'] = abstract.replace('\u00a0', '')
        else:
            item['abstract'] = ""

        total_text = ''
        tags = response.xpath('//div[@class="wpb_wrapper"]/p')
        for tag in tags:
            text = tag.extract()
            if text:
                total_text += delettags(text)
        item['text'] = total_text
        item['price'] = '5000'

        images = []
        images_tags = response.xpath('//dl[@class="gallery-item"]/dt/a')
        if not images_tags:
            images_tags = response.xpath('//div[@class="vc_grid-container-wrapper vc_clearfix"]/div')
            if images_tags:
                options = json.loads(images_tags.xpath('./@data-vc-grid-settings').extract_first())
                formdata ={
                    'action': 'vc_get_vc_grid_data',
                    'vc_action': 'vc_get_vc_grid_data',
                    'tag': 'vc_media_grid',
                    'data[visible_pages]': '5',
                    'data[page_id]': str(options['page_id']),
                    'data[style]': 'all',
                    'data[action]': 'vc_get_vc_grid_data',
                    'data[shortcode_id]': options['shortcode_id'],
                    'data[tag]': options['tag'],
                    'vc_post_id': images_tags.xpath('./@data-vc-post-id').extract_first(),
                    '_vcnonce': images_tags.xpath('./@data-vc-public-nonce').extract_first()
                }
                header = {'Content-Type': 'application/x-www-form-urlencoded'}
                yield FormRequest('http://zenaida.travel/zdat14/wp-admin/admin-ajax.php', self.finalparse, headers=header, formdata=formdata, meta={'item': item})
        else:
            for img in images_tags:
                img_url = img.xpath('./@href').extract_first()
                img_caption = img.xpath('./@data-caption').extract_first()
                if not img_caption:
                    img_caption = img.xpath('./img/@alt').extract_first()
                    if not img_caption:
                        img_caption = ''
                if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
                images.append({"src": img_url.strip(), "caption": img_caption.strip()})

            item['images'] = images

            self.count += 1
            print self.count
            yield item

    def finalparse(self, response):
        item = response.meta['item']
        images_tags = response.xpath('//div[@class="vc_grid-item-mini vc_clearfix "]/div/div/a')
        images = []
        for img in images_tags:
            img_url = img.xpath('./@href').extract_first()
            img_caption = img.xpath('./@title').extract_first()
            if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
            if not img_caption:
                img_caption = ''
            images.append({"src": img_url.strip(), "caption": img_caption.strip()})

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
