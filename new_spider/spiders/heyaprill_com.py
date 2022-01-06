# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree
from datetime import datetime
from scrapy.http import TextResponse
import winpaths
import PyPDF2

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.*?<\/script>', '', text)
    return text

def imagefilter(text):
    img_url = text
    if '.jpg?' in img_url:
        img_url = img_url.split('.jpg?')[0] + '.jpg'
    elif '.png?' in img_url:
        img_url = img_url.split('.png?')[0] + '.png'
    elif '.jpeg?' in img_url:
        img_url = img_url.split('.jpeg?')[0] + '.jpeg'
    elif '.jpg.' in img_url:
        img_url = img_url.split('.jpg.')[0] + '.jpg'
    elif '.png.' in img_url:
        img_url = img_url.split('.png.')[0] + '.png'
    elif '.jpeg.' in img_url:
        img_url = img_url.split('.jpeg.')[0] + '.jpeg'

    img_url = re.sub('-\d+x\d+', '', img_url)
    return img_url


class heyaprill_comSpider(Spider):
    name = "heyaprill_com"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = 'https://www.heyaprill.com/sitemap_index.xml'
    datetime_object = None

    total_cat_urls = []
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)

    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Cookie': '_ga=GA1.2.1677180131.1600478645; _gid=GA1.2.1228418030.1600478645; __asc=949a2865174a3f60b834867dd53; __auc=949a2865174a3f60b834867dd53; _jsuid=103813193; unpoco_66428126=1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
    }

    def start_requests(self):

        yield Request(self.start_url, self.parse1, meta={'page': 1}, headers=self.header)

    def parse1(self, response):
        txt = response.text.replace('\t', '').replace('\n', '')

        cat_urls = re.findall('<sitemap><loc>(.*?)<\/loc><lastmod>', txt)

        for url in cat_urls:

            # url = 'https://www.heyaprill.com/post_tag-sitemap1.xml'
            yield Request(url, self.parse2, meta={'page': 1}, headers=self.header)

            # break

    def get_cat_urls(self, li_tag):
        li_tags = li_tag.xpath('./ul/li')
        for li_tag_1 in li_tags:
            if li_tag_1.xpath('./ul/li'):
                self.get_cat_urls(li_tag_1)
            else:
                href = li_tag_1.xpath('./a/@href').extract_first()
                self.total_cat_urls.append(href)

    def parse2(self, response):
        txt = response.text.replace('\t', '').replace('\n', '')

        cat_urls = re.findall('<url><loc>(.*?)<\/loc><lastmod>', txt)

        for url in cat_urls:

            # for test
            # url = 'https://www.heyaprill.com/maskne/'

            yield Request(url, self.parse, headers=self.header)

            # break

    def parse(self, response):
        page_type = response.xpath('//meta[@property="og:type"]/@content').extract_first()
        if page_type != 'article':
            return
        if not response.xpath('//meta[@property="article:published_time"]/@content').extract_first():
            other_urls = response.xpath('//div[contains(@class,"entry-content ")]/a/@href').extract()
            for url in other_urls:
                yield Request(url, self.parse, headers=self.header)
            return


        post_id = response.xpath('//div[@class="entry-content"]/div/@data-post-id').extract_first()
        # java_script = response.xpath('//script[contains(text(), "var rtb_sync = ")]/text()').extract_first()
        item = OrderedDict()
        keys_texts = response.xpath('//p[@id="tags"]/span/a/text()').extract()
        keywords = []
        for key in keys_texts:
            if len(key) > 50: continue
            keywords.append({'keyword': key.strip()})
        item['keywords'] = keywords
        title = response.xpath('//h1[@class="entry-title"]/text()').extract_first()
        # if not title:
        #     title = response.xpath('//td[@class="f2"]/text()').extract_first()
        item['title'] = title.strip()
        item['url'] = response.url
        contributor = response.xpath('//div[@id="author-bio"]/h3/a/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]

        date = response.xpath('//meta[@property="article:published_time"]/@content').extract_first().split('+')[0]
        if date:
            item['articleDate'] = date.strip()

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()

        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract

        images = []

        img_urls = response.xpath('//div[@class="entry-content"]//img')
        # img_urls_1 = response.xpath('//figure[@class="wp-block-image size-large"]/img')
        # img_urls.extend(img_urls_1)
        for img_tag in img_urls:
            img_url = img_tag.xpath('./@src').extract_first()
            if not img_url:
                continue
            if ('.svg' in img_url) or ('.gif' in img_url) or ('heyaprill.com' not in img_url):
                continue
            img_url = imagefilter(img_url)
            if len(img_url) < 300:
                caption = img_tag.xpath('./@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                images.append({"src": img_url, "caption": caption.strip()})

        tags = response.xpath('//div[@class="entry-content"]/*')
        total_text = ''
        for i, tag in enumerate(tags):
            images_tag = tag.xpath('.//img')
            tag_name = tag.root.tag
            if tag_name != 'div' and tag_name != 'figure' and tag_name != 'img':
            #     for image in images_tag:
            #         img_url = image.xpath('./@src').extract_first()
            #         img_url = imagefilter(response.urljoin(img_url))
            #         if not img_url or len(img_url) > 300: continue
            #         img_caption = image.xpath('./@src').extract_first()
            #         if len(img_caption) > 700:
            #             img_caption = img_caption[0:700]
            #         else:
            #             img_caption = ''
            #         images.append({"src": img_url, "caption": img_caption})
            # else:
                # if tag_name != "div":
                text = tag.extract()
                total_text += delettags(text.replace('\n', ''))

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

        item['images'] = images
        item['themes'] = [{"Id": 0, "ArticleId": 0, "Theme": "United States"}]

        self.count += 1
        print self.count
        yield item

    def filter_content(self, txt):
        temp_array = re.findall('\?ixlib(.*?)"', txt)
        for temp in temp_array:
            if ', http' in temp:
                continue
            txt = txt.replace('?ixlib' + temp, '')

        temp_array = re.findall('\?ixlib(.*?),', txt)
        for temp in temp_array:
            if '" size' in temp:
                continue
            txt = txt.replace('?ixlib' + temp, '')

        temp_array = re.findall('\?ixlib(.*?)"', txt)
        for temp in temp_array:
            if ', http' in temp:
                continue
            txt = txt.replace('?ixlib' + temp, '')
        return txt
