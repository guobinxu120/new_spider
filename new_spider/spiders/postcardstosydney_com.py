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


class postcardstosydney_comSpider(Spider):
    name = "postcardstosydney_com"
    count = 0
    start_url = 'https://postcardstosydney.com/page/1/'
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)


    def start_requests(self):
        yield Request(self.start_url, self.parse, meta={'page': 1})

    def parse(self, response):
        urls = response.xpath('//main[@id="main"]/article/header/div[@class="featured-image"]/a/@href').extract()
        if not urls:
            return
        for url in urls:

            ### for test
            # url = 'https://postcardstosydney.com/2018/04/05/how-to-travel-on-a-low-fodmap-wheat-free-diet/'
            ###########

            yield Request(response.urljoin(url), self.parse_products)
            # break
        response.meta['page'] += 1
        next_url = 'https://postcardstosydney.com/page/' + str(response.meta['page']) + '/'
        yield Request(next_url, self.parse, meta=response.meta)

    def parse_products(self, response):
        item = OrderedDict()
        keys_texts = response.xpath('//span[@class="tags-links"]/a/text()').extract()
        keywords = []
        key_temps = []
        for txt in keys_texts:
            txt = txt.replace('#', '')
            # keys = txt.split('|')
            # for i, key in enumerate(keys):
            #     if not key.strip() in key_temps and len(key) < 50:
            keywords.append({'keyword': txt.strip()})
            key_temps.append(txt.strip())

        # if not keys_texts:
        #     return

        item['keywords'] = keywords
        item['title'] = response.xpath('//head/title/text()').extract_first()
        item['url'] = response.url
        contributor = response.xpath('//meta[@property="article:author"]/@content').extract_first()
        item['contributors'] = [{"contributor": 'ashditerlizzi'}]

        item['articleDate'] = response.xpath('//meta[@property="article:published_time"]/@content').extract_first()
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
        mainimg_url = response.xpath('//div[@class="featured-header-image"]/a/img/@src').extract_first()
        if mainimg_url:
            # mainimg_url = response.urljoin(mainimg_url)
            mainimg_url = imagefilter(mainimg_url)
            caption = response.xpath('//div[@class="featured-header-image"]/a/img/@alt').extract_first()
            if not caption:
                caption = ''
            elif len(caption) > 700:
                caption = caption[0:700]
            if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                images.append({"src": mainimg_url, "caption": caption})

        tags = response.xpath('//div[@class="entry-content"]/div[@class="x_WordSection1"]/*')
        if not tags:
            tags = response.xpath('//div[@class="entry-content"]/*')
        total_text_list = []
        isPassUlTag = False
        while True:
            for tag in tags:
                t = tag.extract()
                if t == '</div>' or t == '</img>' or t[:6] == '<style' or t[:4] == '<nav' or t[:7] == '<script':
                    continue
                if t[:3] == '<ol':
                    self.get_content(tag.xpath('./li/*'), images, total_text_list)
                else:
                    if ('<figure' in t) or ('<amp-img' in t):
                        mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                        caption = tag.xpath('.//img/@data-image-title').extract_first()
                        if mainimg_url:
                            mainimg_url = imagefilter(mainimg_url)

                            if not caption:
                                caption = ''
                            elif len(caption) > 700:
                                caption = caption[0:700]
                            if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                                images.append({"src": mainimg_url, "caption": caption})
                        else:
                            pass

                        continue

                    if (t[:4] == '<h2>'):
                        mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                        caption = tag.xpath('.//img/@data-image-title').extract_first()
                        if mainimg_url:
                            mainimg_url = imagefilter(mainimg_url)

                            if not caption:
                                caption = ''
                            elif len(caption) > 700:
                                caption = caption[0:700]
                            if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                                images.append({"src": mainimg_url, "caption": caption})
                            # continue
                        else:
                            pass

                    if (t[:2] == '<p'):
                        mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                        caption = tag.xpath('.//img/@data-image-title').extract_first()
                        if mainimg_url:
                            mainimg_url = imagefilter(mainimg_url)

                            if not caption:
                                caption = ''
                            elif len(caption) > 700:
                                caption = caption[0:700]
                            if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                                images.append({"src": mainimg_url, "caption": caption})
                            # continue
                        else:
                            pass

                    if ('<div class="tiled-gallery' in t):
                        for img_tag in tag.xpath('.//img'):
                            mainimg_url = img_tag.xpath('./@data-orig-file').extract_first()
                            caption = img_tag.xpath('./@data-image-title').extract_first()
                            if mainimg_url:
                                mainimg_url = imagefilter(mainimg_url)

                                if not caption:
                                    caption = ''
                                elif len(caption) > 700:
                                    caption = caption[0:700]
                                if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                                    images.append({"src": mainimg_url, "caption": caption})
                            else:
                                pass
                        continue

                # if t[:4] == '<img' or t[:3] == '<h1' or t == '</div>' or t == '</img>' or t[:6] == '<style' or t[:4] == '<nav':
                #     continue
                # if t[:3] == '<ul':
                #     isPassUlTag = True
                #     continue
                # elif t == '</ul>':
                #     isPassUlTag = False
                #     continue
                #
                # if isPassUlTag:
                #     continue



                if t[:2] == '<p' or t[:3] == '<h2' or t[:3] == '<ol':
                    t = t.replace('\n', '')
                    tt = delettags(t)
                    total_text_list.append(tt)
            if total_text_list or images:
                break
            else:
                pass
            tags = response.xpath('//div[@class="entry-content"]/div[1]/*')



        total_text = '\n'.join(total_text_list)

        item['text'] = total_text
        item['price'] = '5000'

        item['images'] = images

        self.count += 1
        print self.count
        yield item

    def get_content(self, tags, images, total_text_list):
        for tag in tags:
            t = tag.extract()
            if t == '</div>' or t == '</img>' or t[:6] == '<style' or t[:4] == '<nav' or t[:7] == '<script':
                continue
            if ('<figure' in t) or ('<amp-img' in t):
                mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                caption = tag.xpath('.//img/@data-image-title').extract_first()
                if mainimg_url:
                    mainimg_url = imagefilter(mainimg_url)

                    if not caption:
                        caption = ''
                    elif len(caption) > 700:
                        caption = caption[0:700]
                    if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                        images.append({"src": mainimg_url, "caption": caption})
                else:
                    pass

                continue

            if (t[:4] == '<h2>'):
                mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                caption = tag.xpath('.//img/@data-image-title').extract_first()
                if mainimg_url:
                    mainimg_url = imagefilter(mainimg_url)

                    if not caption:
                        caption = ''
                    elif len(caption) > 700:
                        caption = caption[0:700]
                    if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                        images.append({"src": mainimg_url, "caption": caption})
                    # continue
                else:
                    pass

            if (t[:2] == '<p'):
                mainimg_url = tag.xpath('.//img/@data-orig-file').extract_first()
                caption = tag.xpath('.//img/@data-image-title').extract_first()
                if mainimg_url:
                    mainimg_url = imagefilter(mainimg_url)

                    if not caption:
                        caption = ''
                    elif len(caption) > 700:
                        caption = caption[0:700]
                    if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                        images.append({"src": mainimg_url, "caption": caption})
                    # continue
                else:
                    pass

            if ('<div class="tiled-gallery' in t):
                for img_tag in tag.xpath('.//img'):
                    mainimg_url = img_tag.xpath('./@data-orig-file').extract_first()
                    caption = img_tag.xpath('./@data-image-title').extract_first()
                    if mainimg_url:
                        mainimg_url = imagefilter(mainimg_url)

                        if not caption:
                            caption = ''
                        elif len(caption) > 700:
                            caption = caption[0:700]
                        if len(mainimg_url) < 300 and not '.gif' in mainimg_url:
                            images.append({"src": mainimg_url, "caption": caption})
                    else:
                        pass
                continue

            # if t[:4] == '<img' or t[:3] == '<h1' or t == '</div>' or t == '</img>' or t[:6] == '<style' or t[:4] == '<nav':
            #     continue
            # if t[:3] == '<ul':
            #     isPassUlTag = True
            #     continue
            # elif t == '</ul>':
            #     isPassUlTag = False
            #     continue
            #
            # if isPassUlTag:
            #     continue

            # if t[:2] == '<p' or t[:3] == '<h2':
            #     t = t.replace('\n', '')
            #     tt = delettags(t)
            #     total_text_list.append(tt)
