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


class theconversation_comSpider(Spider):
    name = "theconversation_com"
    count = 0
    custom_output = True
    start_url = 'https://theconversation.com/au'
    datetime_object = None
    use_selenium = False
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        dt = datetime.fromtimestamp(993859200000000000 // 1000000000)
        date_time = dt.strftime("%Y-%m-%d")

        # file = open('E:/R55431102_UCS0007FX_12518467_PDF.pdf', 'rb')
        # fileReader = PyPDF2.PdfFileReader(file)
        # pageObj = fileReader.getPage(0)
        # # a = pageObj.extractText()
        # # print the number of pages in pdf file
        # print(fileReader.numPages)
        # print(pageObj.extractText())
        datetime_str = '03/01/21 00:00:00'

        self.datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
        yield Request(self.start_url, self.parse1, meta={'page': 1})

    def parse1(self, response):
        url_tags = response.xpath('//nav[@id="primary-navigation"]/ol/li/a')
        if not url_tags:
            return
        for url_tag in url_tags:
            url = url_tag.xpath('./@href').extract_first()
            cat_title = url_tag.xpath('./text()').extract_first()
            if cat_title:
                cat_title = cat_title.strip()
            ### for test
            # url = '/the-world-may-lose-half-its-sandy-beaches-by-2100-its-not-too-late-to-save-most-of-them-132586'
            ###########

            yield Request(response.urljoin(url) + '/articles', self.parse, meta={'page': 1, 'cat': response.urljoin(url), 'cat_title': cat_title})

            # break

    def parse(self, response):
        if response.meta['page'] > 5:
            return
        urls = response.xpath('//section[@class="content-list grid-six"]/article/header/div/h2/a/@href').extract()
        if not urls:
            return
        for url in urls:

            ### for test
            # url = '/parasites-win-is-the-perfect-excuse-to-get-stuck-into-genre-bending-and-exciting-korean-cinema-131548'
            ###########

            yield Request(response.urljoin(url), self.parse_products, meta={'url': url, 'cat_title': response.meta['cat_title']})
            # break
        response.meta['page'] += 1
        next_url = response.meta['cat'] + '/articles?page=' + str(response.meta['page'])
        yield Request(next_url, self.parse, meta=response.meta)

    def parse_products(self, response):
        item = OrderedDict()
        keys_text = response.xpath('//meta[@name="news_keywords"]/@content').extract_first()
        if keys_text:
            keys_texts = keys_text.split(',')
            keywords = []
            key_temps = []
            for txt in keys_texts:
                # txt = txt.strip()
                # keys = txt.split('|')
                # for i, key in enumerate(keys):
                #     if not key.strip() in key_temps and len(key) < 50:
                keywords.append({'keyword': txt.strip()})
                key_temps.append(txt.strip())

        # if not keys_texts:
        #     return

            item['keywords'] = keywords
        item['title'] = response.xpath('//h1[@itemprop="name"]/strong/text()').extract_first().strip()
        item['url'] = response.url
        contributor = response.xpath('//meta[@name="author"]/@content').extract_first()
        item['contributors'] = [{"contributor": contributor}]

        articleDate = response.xpath('//meta[@name="pubdate"]/@content').extract_first()
        was_date1_before = False
        if articleDate:
            datetime_object1 = datetime.strptime(articleDate, '%Y%m%d')
            articleDate = datetime_object1.strftime("%Y-%m-%d")

            was_date1_before = self.datetime_object > datetime_object1
        if was_date1_before:
            return
        item['articleDate'] = articleDate
        if not item['articleDate']:
            item['articleDate'] = response.xpath('//time[contains(@class,"entry-date")]/@datetime').extract_first()

        abstract = response.xpath('//meta[@name="description"]/@content').extract_first()
        if abstract:
            item['abstract'] = abstract
        else:
            item['abstract'] = ""
        images = []
        mainimg_url = response.xpath('//figure[@class="magazine"]/div/img/@src').extract_first()
        caption = response.xpath('//figure[@class="magazine"]/div/img/@alt').extract_first()
        if not caption:
            caption = ''

        # if not mainimg_url:
        #     mainimg_url = response.xpath('//figure//img[@itemprop="image"]/@data-src').extract_first()
        #     caption = response.xpath('//figure//img[@itemprop="image"]/@alt').extract_first()
        # if not mainimg_url:
        #     mainimg_url = response.xpath('//div[@itemprop="articleBody"]//figure[@class="align-center zoomable"]//img/@src').extract_first()
        #     if not mainimg_url or mainimg_url[: 4] != 'http':
        #         mainimg_url = response.xpath('//div[@itemprop="articleBody"]//figure[@class="align-center zoomable"]//img/@data-src').extract_first()
        #     caption = response.xpath('//div[@itemprop="articleBody"]//figure[@class="align-center zoomable"]//img/@alt').extract_first()
        #
        # if mainimg_url:
        #     mainimg_url = imagefilter(mainimg_url)
        #     if not caption:
        #         caption = ''
        #     elif len(caption) > 700:
        #         caption = caption[0:700]
        #     if len(mainimg_url) < 300 and '.gif' not in mainimg_url:
        #         images.append({"src": mainimg_url, "caption": caption})
        #     item['images'] = images
        # else:
        #     item['images'] = images
        #     print("No Images")
        #     pass

        yield Request("https://theconversation.com/share/" + response.meta['url'], self.parse_republish, meta={'item': item, 'cat_title': response.meta['cat_title']})

    #         yield Request(item['url'], self.parse1, meta={'item':item}, dont_filter=True)
    def parse_republish(self, response):
        item = response.meta['item']
        republish_content = response.xpath('//section[@class="basic"]/textarea[@class="stolen-body"]').extract_first()

        total_text = ''

        images = []
        if republish_content:
            republish_content = republish_content.replace('\n', '').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;amp;', '&').replace('&amp;', '&')
            republish_content = republish_content.replace('<textarea class="stolen-body" name="non-attributed-body">', '')
            republish_content = republish_content[:len(republish_content) - 11]

            t_array = re.findall('<h1 class="legacy">(.*?)<\/h1>', republish_content)
            if t_array:
                title = t_array[0]
                item['title'] = title
                republish_content = republish_content.replace('<h1 class="legacy">' + title + '</h1>', '').strip()
                if republish_content[:7] == '<figure':
                    temp_array = re.findall('<figure(.*?)figure>', republish_content)
                    if temp_array:
                        figure_str = temp_array[0]
                        mainimg_url = re.findall('<img src="(.*?)\?', figure_str)[0]

                        resp1 = TextResponse(url='',
                                        body='<figure' + figure_str + 'figure>',
                                        encoding='utf-8')
                        caption = resp1.xpath('//span[@class="caption"]/text()').extract_first()
                        if not caption:
                            caption = resp1.xpath('//figcaption//text()').extract_first()
                            if caption:
                                caption = caption.strip()
                        img_contributor = resp1.xpath('//span[@class="attribution"]//text()').extract()
                        if not img_contributor:
                            img_contributor = ''
                        else:
                            img_contributor_array = []
                            for i_c in img_contributor:
                                img_contributor_array.append(i_c.strip())
                            img_contributor = ' '.join(img_contributor_array)

                        mainimg_url = imagefilter(mainimg_url)
                        if not caption:
                            caption = ''
                        elif len(caption) > 700:
                            caption = caption[0:700]
                        if len(mainimg_url) < 300 and '.gif' not in mainimg_url:
                            images.append({"src": mainimg_url, "caption": caption, 'contributor': img_contributor})

                            republish_content = republish_content.replace('<figure' + figure_str + 'figure>', '')
            # total_text = self.filter_content(republish_content)
            total_text = republish_content

            if not images:
                t_array = re.findall('<figure>(.*?)<\/figure>', total_text)
                if t_array:
                    figure_str = t_array[0]
                    # t_array = re.findall('src="(.*?)\?', temp)
                    if len(re.findall('<img src="(.*?)\?', figure_str)) > 0:
                        mainimg_url = re.findall('<img src="(.*?)\?', figure_str)[0]
                        resp1 = TextResponse(url='',
                                        body='<figure>' + figure_str + '</figure>',
                                        encoding='utf-8')
                        caption = resp1.xpath('//span[@class="caption"]/text()').extract_first()
                        if not caption:
                            caption = resp1.xpath('//figcaption//text()').extract_first()
                            if caption:
                                caption = caption.strip()
                        img_contributor = resp1.xpath('//span[@class="attribution"]//text()').extract()
                        if not img_contributor:
                            img_contributor = ''
                        else:
                            img_contributor_array = []
                            for i_c in img_contributor:
                                img_contributor_array.append(i_c.strip())
                            img_contributor = ' '.join(img_contributor_array)

                        mainimg_url = imagefilter(mainimg_url)
                        if not caption:
                            caption = ''
                        elif len(caption) > 700:
                            caption = caption[0:700]
                        if len(mainimg_url) < 300 and '.gif' not in mainimg_url:
                            images.append({"src": mainimg_url, "caption": caption, 'contributor': img_contributor})
                            total_text = total_text.replace('<figure>' + figure_str + '</figure>', '')

                    if not images:
                        t_array = re.findall('<figure class="align-center zoomable"(.*?)<\/figure>', total_text)
                        if t_array:
                            figure_str = t_array[0]
                            # t_array = re.findall('src="(.*?)\?', temp)
                            if len(re.findall('<img src="(.*?)\?', figure_str)) > 0:
                                mainimg_url = re.findall('<img src="(.*?)\?', figure_str)[0]
                                resp1 = TextResponse(url='',
                                                body='<figure class="align-center zoomable"' + figure_str + '</figure>',
                                                encoding='utf-8')
                                caption = resp1.xpath('//span[@class="caption"]/text()').extract_first()
                                if not caption:
                                    caption = resp1.xpath('//figcaption//text()').extract_first()
                                    if caption:
                                        caption = caption.strip()
                                img_contributor = resp1.xpath('//span[@class="attribution"]//text()').extract()
                                if not img_contributor:
                                    img_contributor = ''
                                else:
                                    img_contributor_array = []
                                    for i_c in img_contributor:
                                        img_contributor_array.append(i_c.strip())
                                    img_contributor = ' '.join(img_contributor_array)

                                mainimg_url = imagefilter(mainimg_url)
                                if not caption:
                                    caption = ''
                                elif len(caption) > 700:
                                    caption = caption[0:700]
                                if len(mainimg_url) < 300 and '.gif' not in mainimg_url:
                                    images.append({"src": mainimg_url, "caption": caption, 'contributor': img_contributor})
                                    total_text = total_text.replace('<figure class="align-center zoomable"' + figure_str + '</figure>', '')
        author = item['contributors'][0]['contributor']
        if author:
            t_array = re.findall('<span>(.*?)<\/span>', total_text)
            for t_array_item in t_array:
                figure_str = t_array_item
                resp1 = TextResponse(url='',
                                body=figure_str,
                                encoding='utf-8')
                a_text_array = resp1.xpath('//a/text()').extract()
                if author in a_text_array:
                    total_text = total_text.replace('<span>' + figure_str + '</span>', '')

        item['text'] = total_text.replace('<textarea class="stolen-body">', '')
        item['price'] = '0'
        item['images'] = images

        item['themes'] = [{"Id": 0, "ArticleId": 0, "Theme": "Australia"}]

        # with open('data.json', 'w') as outfile:
        #     json.dump(item, outfile)

        self.count += 1
        print self.count
        yield {'item': item, 'cat_title': response.meta['cat_title']}
        # yield item

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
