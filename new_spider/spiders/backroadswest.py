# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re, requests
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
    name = "backroadswest"
    count = 0
    use_selenium = True

    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://cornershopapp.com/api/v1/branches/2364/aisles/C_450/products'

    def start_requests(self):
        # headers = {
        #     'x-api-source': 'pc',
        #     'x-requested-with': 'XMLHttpRequest',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
        # }
        # resp = requests.get('https://shopee.co.id/api/v2/search_items/?by=relevancy&keyword=iphone&limit=50&newest=0&order=desc&page_type=search&version=2', headers=headers)

        # proxy = "http://yongjin:Jin1234%@au.proxymesh.com:31280"
        yield Request(self.start_url, self.parse_products, meta={'index':1})

    def parse(self, response):
        tags = response.xpath('//div[@class="SideCategoryListFlyout"]/ul/li')
        for parent_cat in tags:
            category_texts = parent_cat.xpath('./ul/li/a/@href').extract()
            if category_texts:
                for cat_url in category_texts:
                    yield Request(response.urljoin(cat_url), self.parse_products)
            else:
                cat_url = parent_cat.xpath('./a/@href').extract_first()
                yield Request(response.urljoin(cat_url), self.parse_products)


    def parse_products(self, response):
        urls = response.xpath('//article//h1[@class="post-title entry-title"]/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), self.parse_product)
        index = response.meta['index']
        if index < 7:
            index +=1
            url = self.start_url+'page/{}'.format(index)
            yield Request(response.urljoin(url), self.parse_products, meta={'index':index})

    def parse_product(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//meta[@itemprop="keywords"]/@content').extract_first()
        keywords = []
        if keys_texts:
            keys = keys_texts.split(',')
            for key in keys:
                if len(key) > 50: continue
                keywords.append({'keyword': key.strip()})

        item['keywords'] = keywords
        title = response.xpath('//h1[@class="post-title entry-title"]/text()').extract_first()
        if not title:
            title = response.xpath('//h1[@class="post-title entry-title"]/a/text()').extract_first()
        item['title'] = title
        item['url'] = response.url
        # contributor = response.xpath('//div[@class="ProductDetailsGrid prodAccordionContent"]/div/div[@class="Value"]/text()').extract_first()
        # if contributor:
        #     contributors = []
        #     for con in contributor.split(','):
        #         contributors.append({"contributor": con.strip()})
        #     item['contributors'] = contributors
        # else:
        #     item['contributors'] = [{"contributor": ''}]

        date = response.xpath('//time[@class="post-date entry-date updated"]/@datetime').extract_first()
        if date:
            item['articleDate'] = date



        abstract = response.xpath('//meta[@itemprop="description"]/@content').extract_first()
        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract


        images = []
        # image_tags = response.xpath('//div[@class="TinyOuterDiv"]/div/a')
        # for img_tag in image_tags:
        #     img_text = img_tag.xpath('./@rel').extract_first()
        #     if img_text:
        #         img_url = json.loads(img_text)['largeimage']
        #         img_url = imagefilter(img_url)
        #         if not img_url or len(img_url) > 300: continue
        #         img_caption = img_tag.xpath('./img/@title').extract_first()
        #         if not img_caption:
        #             img_caption = ''
        #         if len(img_caption) > 700:
        #             img_caption = img_caption[0:700]
        #         images.append({"src": img_url, "caption": img_caption})

        tags = response.xpath('//div[@data-gutter="gutter-default"]')
        total_text = ''

        for i, tag in enumerate(tags):
            if i == len(tags) - 2: break
            text = tag.extract()
            total_text += delettags(text)

            image_tags = tag.xpath('.//img')
            for img_tag in image_tags:
                img_url = img_tag.xpath('./@src').extract_first()
                img_url = imagefilter(img_url)
                if not img_url or len(img_url) > 300: continue
                img_caption = img_tag.xpath('./@alt').extract_first()
                if not img_caption:
                    img_caption = img_tag.xpath('./@title').extract_first()
                    if not img_caption:
                        img_caption = ''

                img_temp_caption = img_tag.xpath(
                    './parent::div/following-sibling::div[@class="slide-content"]/text()').extract_first()
                if img_temp_caption:
                    img_caption = img_temp_caption.strip()
                if len(img_caption) > 700:
                    img_caption = img_caption[0:700]
                images.append({"src": img_url, "caption": img_caption})

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

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
