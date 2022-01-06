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

def imagefilter(text):
    img_url = text
    if '.jpg?' in img_url:
        img_url = img_url.split('.jpg?')[0] + '.jpg'
    elif '.png?' in img_url:
        img_url = img_url.split('.png?')[0] + '.png'
    elif '.jpeg?' in img_url:
        img_url = img_url.split('.jpeg?')[0] + '.jpeg'
    return img_url


class dasoertlicheSpider(Spider):
    name = "travtasy_com"
    count = 0
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://www.travtasy.com/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        xssi = response.body.split("window['__wavt'] = '")[-1].split("';_WidgetManager._Init")[0]
        urls = response.xpath('//div[@id="BlogArchive1_ArchiveList"]/ul/li/ul/li/a[@class="post-count-link"]/@href').extract()
        xssi = xssi.replace(':', '%3A')

        for url in urls:
            url = url.replace('/', '%2F').replace(':', '%3A')
            created_url = 'https://www.travtasy.com/?action=getTitles&widgetId=BlogArchive1&widgetType=BlogArchive&responseType=js&path={}&xssi_token={}'.format(url, xssi)
            yield Request(created_url, self.parse1)
            # break

        # tags = response.xpath('//ul[@id="primary-menu"]/li')
        # for parent_cat in tags:
        #     category_text = parent_cat.xpath('./a/text()').extract_first()
        #     if category_text == 'Home' or category_text == "About" or category_text == "Contact": continue
        #     sub_cats = parent_cat.xpath('./ul/li/a/@href').extract()
        #     if sub_cats:
        #         for cat_url in sub_cats:
        #             yield Request(response.urljoin(cat_url), self.parse_products)
        #     else:
        #         cat_url = parent_cat.xpath('./a/@href').extract_first()
        #         yield Request(response.urljoin(cat_url), self.parse_products)

        # for i in range(1, 11):
        #     if i == 1:
        #         yield Request(self.start_url, self.parse_products)
        #     else:
        #         yield Request(self.start_url+'page/{}/'.format(i), self.parse_products)

    def parse1(self, response):
        urls = response.body.split("'url': '")
        for url in urls:
            if url[:5] == 'https':
                url = url.split("'}")[0]
                yield Request(url, self.parse_products)
                # break

        # data = re.findall("'getTitles',(.*?)\);", response.body)[0]
        # jsondata = json.loads(re.findall("'getTitles',(.*?)\);", response.body)[0])
        # for parent_cat in urls:
        #     yield Request(response.urljoin(parent_cat), self.parse_products)
        #     # yield Request('https://emptynesterstravelinsights.com/two-days-in-lucerne/', self.parse_products)

    def parse_products(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//div[@class="theme-posts-tag"]/ul[@class="tags"]/li/a/text()').extract()
        keywords = []
        key_temps = []
        for txt in keys_texts:
            txt = txt.replace('#', '')
            # keys = txt.split('|')
            # for i, key in enumerate(keys):
            #     if not key.strip() in key_temps and len(key) < 50:
            keywords.append({'keyword': txt.strip()})
            key_temps.append(txt.strip())

        if not keys_texts: return

        item['keywords'] = keywords
        item['title'] = response.xpath('//h1[@itemprop="name headline"]/div/a/text()').extract_first()
        item['url'] = response.url
        contributor = response.xpath('//a[@rel="author"]/span/text()').extract_first()
        item['contributors'] = [{"contributor": contributor}]

        item['articleDate'] = response.xpath('//abbr[@itemprop="datePublished"]/@title').extract_first()
        if not item['articleDate']:
            item['articleDate'] = response.xpath('//time[contains(@class,"entry-date")]/@datetime').extract_first()

    #         yield Request(item['url'], self.parse1, meta={'item':item}, dont_filter=True)
    # def parse1(self, response):

        # item = response.meta['item']
        abstract = response.xpath('//meta[@name="description"]/@content').extract_first()
        if abstract:
            item['abstract'] = abstract
        else:
            item['abstract'] = ""

        images = []
        mainimg_url = response.xpath('//div[@class="theme-posts-text"]/img/@src').extract_first()
        if mainimg_url and 'https://lh3.googleusercontent.com/' not in mainimg_url:
            mainimg_url = imagefilter(mainimg_url)
            caption = response.xpath('//div[@class="theme-posts-text"]/img/@alt').extract_first()
            if not caption:
                caption = ''
            elif len(caption) > 700:
                caption = caption[0:700]
            if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                images.append({"src": mainimg_url, "caption": caption})

        tags = response.xpath('//div[@class="theme-posts-text"]').extract_first().split('\n')
        total_text_list = []
        isPassUlTag = False
        for t in tags:
            if t[:4] == '<img' or t[:4] == '<div' or t[:3] == '<h1' or t == '</div>' or t == '</img>' or t[:6] == '<style':
                continue
            if t[:3] == '<ul':
                isPassUlTag = True
                continue
            elif t == '</ul>':
                isPassUlTag = False
                continue

            if isPassUlTag:
                continue

            total_text_list.append(t)


        total_text = '\n'.join(total_text_list)

        # for tag in tags:
        #     tag_name = tag._root.tag
        #     imgs = tag.xpath('.//img')
        #     if tag_name.lower() == 'div' and not imgs: continue
        #     if tag_name.lower() == 'figure' or imgs or tag_name.lower() == 'img':
        #         img_url = tag.xpath('.//img/@data-orig-file').extract_first()
        #         if tag_name.lower() == 'img':
        #             img_url = tag.xpath('./@data-orig-file').extract_first()
        #         if not img_url or len(img_url) > 300 or '.gif' in img_url: continue
        #         img_url = imagefilter(img_url)
        #
        #         img_caption = tag.xpath('./figcaption/text()').extract_first()
        #         if not img_caption:
        #             img_caption = tag.xpath('./img/@alt').extract_first()
        #         if not img_caption:
        #             img_caption = tag.xpath('/@alt').extract_first()
        #         if not img_caption:
        #             img_caption = ''
        #
        #         images.append({"src": img_url, "caption": img_caption})
        #         if tag_name == 'p' and ''.join(tag.xpath('./text()').extract()).strip() != '':
        #             try:
        #                 total_text +='<p>{}</p>'.format(''.join(tag.xpath('./text()').extract()).strip().replace(u'\xa0', ' '))
        #             except:
        #                 pass
        #     else:
        #         tag_text = tag.xpath('./text()').extract_first()
        #         # if tag_name.lower() == 'noscript': continue
        #         if tag_text and tag_name == 'p' and 'Read also:' in tag_text: break
        #         text = tag.extract()
        #         total_text += delettags(text)

        item['text'] = total_text
        item['price'] = '50'

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
