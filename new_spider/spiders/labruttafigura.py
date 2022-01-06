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
    name = "labruttafigura"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://www.labruttafigura.com/'

    def start_requests(self):
        yield Request(self.start_url, self.parse1, meta={'index':5})

    def parse(self, response):
        parent_tags = response.xpath('//ul[@class="menu"]/li')
        url_list = []
        for parent in parent_tags:
            urls = parent.xpath('.//ul[@class="sub-menu"]/li/a/@href').extract()
            if urls:
                for url in urls:
                    if not url in url_list:
                        url_list.append(url)
                        yield Request(response.urljoin(url), self.parse1)
            else:
                url = parent.xpath('./a/@href').extract_first()
                yield Request(response.urljoin(url), self.parse1)


    def parse1(self, response):
        tags = response.xpath('//article/div[@class="thumbnail"]/a/@href').extract()
        if tags:
            for url in tags:
                yield Request(response.urljoin(url), self.parse_product)

        index = response.meta['index']
        if index < 95:
            index += 6
            url = 'https://www.labruttafigura.com/wp-admin/admin-ajax.php'
            formdata = {
                'offset': str(index),
                'layout': 'grid-2',
                'ppp': '6',
                'action': 'penci_more_post_ajax',
                'nonce': '28557b19e0'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
            }

            yield FormRequest(url, self.parse1, formdata=formdata, headers=headers, meta={'index': index})


    def parse_product(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//div[@class="post-tags"]/a/text()').extract()
        keywords = []
        for key in keys_texts:
            if len(key) > 50: continue
            keywords.append({'keyword': key.strip()})
        item['keywords'] = keywords
        title = response.xpath('//h1[@class="post-title single-post-title"]/text()').extract_first()
        # if not title:
        #     title = response.xpath('//td[@class="f2"]/text()').extract_first()
        item['title'] = title.strip()
        item['url'] = response.url
        contributor = response.xpath('//a[@class="author-url"]/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]

        date = ''.join(response.xpath('//div[@class="post-box-meta-single"]/span[2]/text()').extract())
        if date:
            item['articleDate'] = date.strip()

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()

        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract

        images = []

        mainimg_url = response.xpath('//div[@class="post-image"]/a/@href').extract_first()
        if mainimg_url:
            img_url = imagefilter(mainimg_url)
            if len(img_url) < 300:
                caption = response.xpath('//div[@class="post-image"]/a/img/@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                images.append({"src": img_url, "caption": caption})

        tags = response.xpath('//div[@class="inner-post-entry"]/*')
        total_text = ''
        for i, tag in enumerate(tags):
            images_tag = tag.xpath('.//img')
            tag_name = tag._root.tag
            if images_tag:
                for image in images_tag:
                    img_url = image.xpath('./@src').extract_first()
                    img_url = imagefilter(response.urljoin(img_url))
                    if not img_url or len(img_url) > 300: continue
                    img_caption = image.xpath('./@src').extract_first()
                    if len(img_caption) > 700:
                        img_caption = img_caption[0:700]
                    else:
                        img_caption = ''
                    images.append({"src": img_url, "caption": img_caption})
            else:
                # if tag_name != "div":
                text = tag.extract()
                total_text += delettags(text)

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

        item['images'] = images

        self.count += 1
        print self.count
        yield item
