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


class moneyminiblog_comSpider(Spider):
    name = "moneyminiblog_com"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = [
        'https://moneyminiblog.com/article-archives/',
            # 'https://moneyminiblog.com/category/budgeting/',
        # 'https://moneyminiblog.com/category/college/',
        # 'https://moneyminiblog.com/category/credit-cards/',
        # 'https://moneyminiblog.com/category/debt-relief/',
        # 'https://moneyminiblog.com/category/investing/',
        # 'https://moneyminiblog.com/category/mortgage-home/',
        # 'https://moneyminiblog.com/category/save-money/',
        # 'https://moneyminiblog.com/category/creating-habits/',
        # 'https://moneyminiblog.com/category/goal-setting/',
        # 'https://moneyminiblog.com/category/productivity/',
        # 'https://moneyminiblog.com/category/self-discipline/',
        # 'https://moneyminiblog.com/category/complete-guides/',
        # 'https://moneyminiblog.com/read-the-blog/'
    ]
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

    all_post_urls = []

    years = [2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013]

    def start_requests(self):
        for year_val in self.years:
            if year_val == 2020:
                # continue
                yield Request('https://moneyminiblog.com/article-archives/', self.parse1)
            else:
                form_data = {
                    'action': 'extra_timeline_get_content',
                    'timeline_nonce': '6bbb4db138',
                    'last_month': 'january',
                    'last_year': str(year_val + 1),
                    'through_year': str(year_val)
                }

                headers = {
                    'origin': 'https://moneyminiblog.com',
                    'referer': 'https://moneyminiblog.com/article-archives/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }

                yield FormRequest('https://moneyminiblog.com/wp-admin/admin-ajax.php', self.parse1, formdata=form_data, headers=headers)


    def parse1(self, response):
        urls = response.xpath('//div[contains(@class,"timeline-module et_extra_other_module")]//article//h3/a/@href').extract()
        # if not urls:
        #     articles = response.xpath('//div[@id="main-content"]//article')
        if not urls:
            return
        # txt = response.text.replace('\t', '').replace('\n', '')
        #
        # cat_urls = re.findall('<sitemap><loc>(.*?)<\/loc><lastmod>', txt)

        for url in urls:
            if url in self.all_post_urls:
                continue
            self.all_post_urls.append(url)
            yield Request(url, self.parse, meta={'page': 1})

            # break

        # response.meta['page'] += 1
        # origin_url = response.meta['origin_url']
        # yield Request(origin_url + '/page/{}/'.format(str(response.meta['page'])), self.parse1, meta=response.meta)

    def parse(self, response):
        json_data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        graph = json_data.get('@graph')

        # page_type = response.xpath('//meta[@property="og:type"]/@content').extract_first()
        # if page_type != 'article':
        #     return
        # if not response.xpath('//meta[@property="article:published_time"]/@content').extract_first():
        #     other_urls = response.xpath('//div[contains(@class,"entry-content ")]/a/@href').extract()
        #     for url in other_urls:
        #         yield Request(url, self.parse, headers=self.header)
        #     return


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
        contributor = ''
        if graph and len(graph) > 3:
            contributor = graph[3].get('name')
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

        img_urls = response.xpath('//article[@id]//img')
        # img_urls_1 = response.xpath('//figure[@class="wp-block-image size-large"]/img')
        # img_urls.extend(img_urls_1)
        for img_tag in img_urls:
            img_url = img_tag.xpath('./@src').extract_first()
            if not img_url:
                continue
            if ('.svg' in img_url) or ('.gif' in img_url) or ('moneyminiblog.com' not in img_url):
                img_url = img_tag.xpath('./@srcset').extract_first()
                if not img_url:
                    continue
                img_url = img_url.split(',')[0].split(' ')[0]
                if ('.svg' in img_url) or ('.gif' in img_url) or ('moneyminiblog.com' not in img_url):
                    continue
            img_url = imagefilter(img_url)
            if len(img_url) < 300:
                caption = img_tag.xpath('./@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                images.append({"src": img_url, "caption": caption.strip()})

        tags = response.xpath('//div[@class="post-content entry-content"]/*')
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
