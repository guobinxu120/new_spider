# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree
from datetime import datetime
from scrapy.http import TextResponse

def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>|<iframe.*?>|</iframe>', '', text)
    text = re.sub('<script.*?<\/script>', '', text)
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


class onefrazzledmum_comSpider(Spider):
    name = "onefrazzledmum_com"
    count = 0
    custom_output = False
    use_selenium = True
    start_url = [
            'https://onefrazzledmum.com/'
    ]
    datetime_object = None

    total_cat_urls = []
    # def __init__(self, *args, **kwargs):
    #     super(sightseeingshoes_comSpider, self).__init__(*args, **kwargs)

    header = {
        'accept': 'ext/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'cookie': 'cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-non-necessary=yes; gdpr[allowed_cookies]=%5B%5D; CookieLawInfoConsent=eyJuZWNlc3NhcnkiOnRydWUsIm5vbi1uZWNlc3NhcnkiOnRydWV9; viewed_cookie_policy=yes; gdpr[consent_types]=%5B%5D',
        'if-none-match': 'W/"27c87d980cae56de5f7d3d37a3796e55c3a47f7b"',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    total_post_ids = []

    def start_requests(self):
        # a = "2019-10-23T10:47:05-05:00"
        for i in range(73):
            url = 'https://onefrazzledmum.com/page/{}/'.format(str(i + 1))
            yield Request(url, self.parse1, meta={'page': 1}, headers=self.header)

    def parse1(self, response):
        urls = response.xpath('//main[@id="main"]//article')
        if not urls:
            return
        for url_tag in urls:
            url = url_tag.xpath('.//h2[@class="entry-title"]/a/@href').extract_first()
            # url = 'https://www.missirosesviews.com/22061-2/'
            # img_url = url_tag.xpath('.//a[@class="entry-image-link"]/img/@srcset').extract_first()
            # img_url = img_url.split(' ')[0]
            # img_alt = url_tag.xpath('.//a[@class="entry-image-link"]/img/@alt').extract_first()
            if 'http' not in url:
                url = 'https://onefrazzledmum.com/' + url
            yield Request(url, self.parse2, headers=self.header)
            # break

        # next_url = response.xpath('//a[@class="next page-numbers"]/@href').extract_first()
        # if 'http' not in next_url:
        #         next_url = 'https://onefrazzledmum.com/' + next_url
        # if next_url:
        #     yield Request(next_url, self.parse1, meta=response.meta, headers=self.header)

    def parse2(self, response):
        post_id = response.xpath('//body/@class').extract_first().split('postid-')[-1].split(' ')[0]
        # if post_id in self.total_post_ids:
        #     return
        self.total_post_ids.append(post_id)
        # java_script = response.xpath('//script[contains(text(), "var rtb_sync = ")]/text()').extract_first()
        item = OrderedDict()
        keys_texts = response.xpath('//a[@rel="category tag"]/text()').extract()
        # keys_texts.remove('Home')
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
        contributor = response.xpath('//span[@class="author-name"]/text()').extract_first()
        if contributor:
            item['contributors'] = [{"contributor": contributor}]
        else:
            item['contributors'] = [{"contributor": ''}]

        date = response.xpath('//meta[@property="article:published_time"]/@content').extract_first()
        if date:
            item['articleDate'] = date[: len(date) - 6]
        else:
            date = response.xpath('//meta[@property="article:modified_time"]/@content').extract_first()
            if date:
                item['articleDate'] = date[:len(date) - 6]
            else:
                print("no date")

        abstract = response.xpath('//meta[@property="og:description"]/@content').extract_first()

        if abstract:
            if len(abstract) > 1000:
                abstract = abstract[0:1000]
            item['abstract'] = abstract

        images = []

        img_urls = response.xpath('//div[contains(@class,"featured-image")]//img')
        main_img_tag = response.xpath('//div[@itemprop="text"]//img')
        # img_urls_1 = response.xpath('//figure[@class="wp-block-image size-large"]/img')
        # img_urls.extend(img_urls_1)
        if img_urls:
            img_urls.extend(main_img_tag)
        else:
            img_urls = main_img_tag
        temps = []
        # if response.meta['img_url']:
        #     temps.append(response.meta['img_url'])
            # images.append({"src": response.meta['img_url'], "caption": response.meta['img_alt']})
        for img_tag in img_urls:
            img_url = img_tag.xpath('./@src').extract_first()
            # if not img_url:
            #     continue



            # img_url = img_url.strip()
            # if ('missirosesviews.com' not in img_url):
            #     continue

            if (not img_url) or ('.svg' in img_url) or ('.gif' in img_url) or (u'data:image/' in img_url):
                img_url = img_tag.xpath('./@data-src').extract_first()
                if not img_url:
                    img_url = img_tag.xpath('./@srcset').extract_first()
                    if not img_url:
                        continue
                    img_url = img_url.split(' ')[0]
                    if ('.svg' in img_url) or ('.gif' in img_url):
                        continue
                if not img_url:
                    continue
            img_url = imagefilter(img_url)
            if img_url and len(img_url) < 300:
                caption = img_tag.xpath('./@alt').extract_first()
                if caption and len(caption) > 700:
                    caption = caption[0:700]
                if not caption:
                    caption = ''
                img_url = img_url.strip()
                
                if 'campaignmonitor.com' in img_url:
                    continue

                if img_url in temps:
                    continue
                
                if 'http' not in img_url:
                    img_url = 'https://onefrazzledmum.com' + img_url
                temps.append(img_url)

                # img_url = img_url.replace('eattillyoubleed', 'pistouandpastis')
                images.append({"src": img_url, "caption": caption.strip()})

        tags = response.xpath('//div[@itemprop="text"]/*')
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
                text = tag.extract().replace('\n', '')

                text = delettags(text)
                if text == '<p></p>' or text == '<div></div>' or 'id="dpsp-content-top"' in text \
                        or 'class="pgtContainpgt"' in text or 'id="dpsp-content-bottom"' in text \
                        or 'll also like this:' in text or 'Buy it here' in text \
                        or '<iframe' in text or 'the_champ_sharing_container' in text \
                        or 'flight-wrapper' in text:
                    continue
                total_text += text

        item['text'] = delettags(total_text.strip().replace('\t', '').replace('\n', ''))
        item['price'] = '5000'

        item['images'] = images
        item['themes'] = [{"Id": 0, "ArticleId": 0, "Theme": "United Kingdom"}]

        self.count += 1
        print("Total count: " + str(self.count))
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
