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


class hearthandmade_co_ukSpider(Spider):
    name = "hearthandmade_co_uk"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = 'https://www.hearthandmade.co.uk/'
    datetime_object = None

    total_cat_urls = []
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        # file = open('E:/R55431102_UCS0007FX_12518467_PDF.pdf', 'rb')
        # fileReader = PyPDF2.PdfFileReader(file)
        # pageObj = fileReader.getPage(0)
        # # a = pageObj.extractText()
        # # print the number of pages in pdf file
        # print(fileReader.numPages)
        # print(pageObj.extractText())
        datetime_str = '07/20/20 00:00:00'

        self.datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
        yield Request(self.start_url, self.parse1, meta={'page': 1})

    def parse1(self, response):
        li_tag = response.xpath('//ul[@id="menu-top-menu"]/li[1]')
        self.get_cat_urls(li_tag[0])

        for url in self.total_cat_urls:
            yield Request(url, self.parse2, meta={'page': 1})

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

        url_tags = response.xpath('//main[@id="genesis-content"]/article')
        if not url_tags:
            return
        for url_tag in url_tags:
            url = url_tag.xpath('.//h2[@itemprop="headline"]/a/@href').extract_first()
            cat_title = url_tag.xpath('./text()').extract_first()
            if cat_title:
                cat_title = cat_title.strip()
            ### for test
            # url = 'https://www.hearthandmade.co.uk/essential-oils-for-sleep/'
            ###########

            yield Request(response.urljoin(url), self.parse, meta={'page': 1, 'cat': response.urljoin(url), 'cat_title': cat_title})

            # break

        response.meta['page'] += 1
        next_url = response.xpath('//li[@class="pagination-next"]/a/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse2, meta=response.meta)

    def parse(self, response):

        post_id = response.xpath('//div[@class="entry-content"]/div/@data-post-id').extract_first()
        # java_script = response.xpath('//script[contains(text(), "var rtb_sync = ")]/text()').extract_first()
        item = OrderedDict()
        keys_texts = response.xpath('//span[@class="entry-tags"]/a/text()').extract()
        keywords = []
        for key in keys_texts:
            if len(key) > 50: continue
            keywords.append({'keyword': key.strip()})
        item['keywords'] = keywords
        title = response.xpath('//h1[@itemprop="headline"]/text()').extract_first()
        # if not title:
        #     title = response.xpath('//td[@class="f2"]/text()').extract_first()
        item['title'] = title.strip()
        item['url'] = response.url
        contributor = response.xpath('//span[@class="entry-author-name"]/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]

        date = response.xpath('//meta[@property="og:updated_time"]/@content').extract_first().split('+')[0]
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
            if ('.svg' in img_url) or ('.gif' in img_url) or ('hearthandmade.co.uk' not in img_url):
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
                total_text += delettags(text)

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

        item['images'] = images
        item['themes'] = [{"Id": 0, "ArticleId": 0, "Theme": "United Kingdom"}]

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
