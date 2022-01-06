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


class wagthedoguk_comSpider(Spider):
    name = "wagthedoguk_com"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = [
        'https://www.wagthedoguk.com/reviews/',
        'https://www.wagthedoguk.com/wag-cool/',
        'https://www.wagthedoguk.com/dog-news/',
        'https://www.wagthedoguk.com/care/',
        'https://www.wagthedoguk.com/travel-guide/',
        'https://www.wagthedoguk.com/france/',
        'https://www.wagthedoguk.com/hong-kong/',
        'https://www.wagthedoguk.com/italy/',
        'https://www.wagthedoguk.com/switzerland/',
        'https://www.wagthedoguk.com/uk/',
        'https://www.wagthedoguk.com/usa/',
        'https://www.wagthedoguk.com/dog-food-guide/',
        'https://www.wagthedoguk.com/dogtastymeals/',
        'https://www.wagthedoguk.com/treats/'
    ]
    datetime_object = None

    total_cat_urls = []
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in self.start_url:
            yield Request(url, self.parse2, meta={'page': 1})

    def parse2(self, response):
        url_tags = response.xpath('//main[@id="main-content"]//article')
        if not url_tags:
            return
        for url_tag in url_tags:
            url = url_tag.xpath('.//h2/a/@href').extract_first()
            cat_title = url_tag.xpath('./text()').extract_first()
            if cat_title:
                cat_title = cat_title.strip()
            ### for test
            # url = 'https://www.wagthedoguk.com/2012/10/15/oscar-the-globetrotting-dog-visits-more-than-30-countries-photos/'
            ###########

            yield Request(response.urljoin(url), self.parse, meta={'page': 1, 'cat': response.urljoin(url), 'cat_title': cat_title})

            # break

        response.meta['page'] += 1
        next_url = response.xpath('//a[@class="nextpostslink"]/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse2, meta=response.meta)

    def parse(self, response):
        json_str = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        if json_str:
            json_data = json.loads(json_str)
        else:
            json_data = None
        post_id = response.xpath('//div[@class="entry-content"]/div/@data-post-id').extract_first()
        # java_script = response.xpath('//script[contains(text(), "var rtb_sync = ")]/text()').extract_first()
        item = OrderedDict()
        keys_texts = response.xpath('//span[@class="entry-tags"]/a/text()').extract()
        keywords = []
        if json_data:
            for a in json_data['@graph']:
                if a['@type'] == 'Article' and ('keywords' in a.keys()):
                    for key in a['keywords'].split(','):
                        if len(key) > 50: continue
                        keywords.append({'keyword': key.strip()})
        item['keywords'] = keywords
        title = response.xpath('//h1[@class="single-pagetitle"]/text()').extract_first()
        # if not title:
        #     title = response.xpath('//td[@class="f2"]/text()').extract_first()
        item['title'] = title.strip()
        item['url'] = response.url
        contributor = response.xpath('//a[@rel="author"]/text()').extract_first()
        if contributor:
            # if contributor == 'Guest Author':
            #     return
            item['contributors'] = [{"contributor": contributor}]

        date_val = response.xpath('//meta[@property="article:published_time"]/@content').extract_first().split('+')[0]
        if date_val:
            item['articleDate'] = date_val.strip()

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()

        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract

        images = []

        img_urls = response.xpath('//article//p/img') + response.xpath('//article//span/img')

        # img_urls_1 = response.xpath('//figure[@class="wp-block-image size-large"]/img')
        # img_urls.extend(img_urls_1)
        for img_tag in img_urls:
            img_url = img_tag.xpath('./@src').extract_first()
            if (not img_url) or ('amazon' in img_url):
                continue
            if ('.svg' in img_url) or ('.gif' in img_url):
                continue
            img_url = imagefilter(img_url)
            if len(img_url) < 300:
                caption = img_tag.xpath('./@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                images.append({"src": img_url, "caption": caption.strip()})

        tags = response.xpath('//article/div/*')

        total_text = response.xpath('//article/div').extract_first()
        total_text = total_text.replace('\t', '').replace('\n', '')
        # total_text = 'asdfasdf<div fsadfasdfsdfsdfasdf </div>55ffff'
        total_text = total_text.replace('<div class="entry">', '')
        total_text = total_text[:len(total_text) - 6]
        total_text = total_text.replace('<div class="single-postmetadata-divider-top"><div class="divider"></div></div>', '')
        total_text = total_text.replace('<div class="single-postmetadata-divider-bottom"><div class="divider"></div></div>', '')
        total_text = re.sub('<img.*?>', '', total_text)
        total_text = re.sub('<style.*?<\/style>', '', total_text)
        total_text = re.sub('<code.*?<\/code>', '', total_text)
        total_text = re.sub('<noscript.*?<\/noscript>', '', total_text)
        total_text = re.sub('<section.*?<\/section>', '', total_text)
        total_text = re.sub('<nav.*?<\/nav>', '', total_text)
        total_text = re.sub('<iframe.*?<\/iframe>', '', total_text)
        total_text = re.sub('<h6 class="zemanta-related-title".*?<\/h6>', '', total_text)
        total_text = re.sub('<ul class="zemanta-article-ul.*?<\/ul>', '', total_text)
        # total_text = re.sub('<a.*?<\/a>', '', total_text)

        # total_text = re.sub('<div.*?<\/div>', '', total_text)
        # total_text = total_text.replace('</div>', '')
        total_text = total_text.replace('<!-- end postmetadata -->', '')

        # total_text = ''
        # for i, tag in enumerate(tags):
        #     images_tag = tag.xpath('.//img')
        #     tag_name = tag.root.tag
        #     if tag_name != 'div' and tag_name != 'figure' and \
        #             tag_name != 'img' and tag_name != "blockquote" and \
        #             tag_name != "i" and tag_name != "section" and tag_name != "nav":
        #     #     for image in images_tag:
        #     #         img_url = image.xpath('./@src').extract_first()
        #     #         img_url = imagefilter(response.urljoin(img_url))
        #     #         if not img_url or len(img_url) > 300: continue
        #     #         img_caption = image.xpath('./@src').extract_first()
        #     #         if len(img_caption) > 700:
        #     #             img_caption = img_caption[0:700]
        #     #         else:
        #     #             img_caption = ''
        #     #         images.append({"src": img_url, "caption": img_caption})
        #     # else:
        #         # if tag_name != "div":
        #         text = tag.extract()
        #         total_text += delettags(text)

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
