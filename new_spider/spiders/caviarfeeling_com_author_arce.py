# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree
from datetime import datetime
from scrapy.http import TextResponse
import winpaths
import PyPDF2, datetime

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>|<iframe.*?>|</iframe>', '', text)
    text = re.sub('<script.*?<\/script>', '', text)
    # text = re.sub('<span class="has-inline-color has-white-color".*?<\/span>', '', text)
    return text

def imagefilter(text):
    img_url = text.split('?')[0]

    if ('.jpg' not in img_url) and ('.png' not in img_url) \
            and ('.jpeg' not in img_url):
        return ''
    if '#' in img_url:
        img_url = img_url.split('#')[0]

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

    # img_url = re.sub('-\d+x\d+', '', img_url)
    return img_url


class caviarfeeling_com_author_arceSpider(Spider):
    name = "caviarfeeling_com_author_arce"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = [
            # 'https://www.caviarfeeling.com/author/arce',
        'https://www.caviarfeeling.com/author/caviar/',
        'https://www.caviarfeeling.com/author/ana/',
        'https://www.caviarfeeling.com/author/alice/',
        'https://www.caviarfeeling.com/author/sophia/',
        'https://www.caviarfeeling.com/author/hayley/',
        'https://www.caviarfeeling.com/author/rachel/',
        'https://www.caviarfeeling.com/author/rachel-medlock/'
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

    total_post_ids = []

    def start_requests(self):
        # a = "2019-10-23T10:47:05-05:00"
        for url in self.start_url:
            yield Request(url, self.parse1, meta={'page': 1, 'origin_url': url})
            # break

    def parse1(self, response):
        urls = response.xpath('//div[@class="blogpost archive_pages layout_modern sm_images clearfix"]/div/h1/a/@href').extract()
        if not urls:
            return
        for url in urls:
            # url = 'https://www.caviarfeeling.com/post/skin-care-trends-2021-latest/'
            yield Request(url, self.parse, meta={'page': 1, 'origin_url': url})
            # break

        next_url = response.xpath('//a[@class="pagination-next"]/@href').extract_first()
        if next_url:
            yield Request(next_url, self.parse1, meta=response.meta)

    def parse(self, response):
        post_id = response.xpath('//body/@class').extract_first().split('postid-')[-1].split(' ')[0]
        if post_id in self.total_post_ids:
            return
        self.total_post_ids.append(post_id[0])
        # java_script = response.xpath('//script[contains(text(), "var rtb_sync = ")]/text()').extract_first()
        item = OrderedDict()
        keys_texts = response.xpath('//li[@class="category_output"]/a/text()').extract()
        keywords = []
        for key in keys_texts:
            if len(key) > 50: continue
            keywords.append({'keyword': key.strip()})
        item['keywords'] = keywords
        title = response.xpath('//h2[@class="singlepost_title"]/text()').extract_first()
        # if not title:
        #     title = response.xpath('//td[@class="f2"]/text()').extract_first()
        item['title'] = title.strip()
        item['url'] = response.url
        contributor = response.xpath('//a[@rel="author"]/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]
        else:
            item['contributors'] = [{"contributor": ''}]

        date = response.xpath('//meta[@property="og:updated_time"]/@content').extract_first()
        if date:
            item['articleDate'] = date[: len(date) - 6]
        else:
            date = response.xpath('//meta[@property="article:modified_time"]/@content').extract_first()
            if date:
                item['articleDate'] = date[:len(date) - 6].strip()
            else:
                print("no date")

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()

        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract

        images = []

        main_img_tag = response.xpath('//a[@class="single-post-gallery"]/img')
        img_urls = response.xpath('//div[contains(@class,"post-content")]//img')
        # img_urls_1 = response.xpath('//figure[@class="wp-block-image size-large"]/img')
        # img_urls.extend(img_urls_1)
        if main_img_tag:
            img_urls.insert(0, main_img_tag[0])
        temps = []
        for img_tag in img_urls:
            img_url = img_tag.xpath('./@src').extract_first()
            if not img_url:
                continue

            # img_url = img_url.strip()
            # if ('heartrepreneur.com' not in img_url):
            #     continue

            if ('.svg' in img_url) or ('.gif' in img_url) or (u'data:image/' in img_url):
                img_url = img_tag.xpath('./@data-src').extract_first()
                if not img_url:
                    continue
                img_url = "https:" + img_url.split(',')[-1].split(':')[-1]
                if ('.svg' in img_url) or ('.gif' in img_url):
                    continue
            img_url = imagefilter(img_url)
            if img_url and len(img_url) < 300:
                caption = img_tag.xpath('./@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                img_url = img_url.strip()

                if 'https://www.caviarfeeling.com' in img_url:
                    img_url = "https://www.caviarfeeling.com" + img_url.split("https://www.caviarfeeling.com")[-1]
                if img_url.replace('http:', '').replace('https:', '') in temps:
                    continue
                temps.append(img_url.replace('http:', '').replace('https:', ''))

                # img_url = img_url.replace('eattillyoubleed', 'pistouandpastis')
                images.append({"src": img_url, "caption": caption.strip()})

        tags = response.xpath('//div[contains(@class,"post-content")]/*')
        total_text = ''
        for i, tag in enumerate(tags):
            images_tag = tag.xpath('.//img')
            tag_name = tag.root.tag
            if tag_name != 'figure' and tag_name != 'img' and tag_name != 'script' and tag_name != 'style':
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
                text = tag.extract().replace('\n', '').replace('\n', '')
                if 'Non-invasive skin' in text:
                    print('dsdfsd')

                text = delettags(text)
                if text == '<p></p>' or text == '<div></div>' or 'id="primisPlayerContainerDiv' in text \
                        or 'social_icons vertical_sharing clearfix' in text \
                        or 'll also like this:' in text or 'Buy it here' in text \
                        or '<iframe' in text or 'google_ads_iframe' in text \
                        or 'flight-wrapper' in text:
                    continue
                total_text += text

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

        item['images'] = images
        item['themes'] = [{"Id": 0, "ArticleId": 0, "Theme": "Australia"}]

        if item['text']:
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
