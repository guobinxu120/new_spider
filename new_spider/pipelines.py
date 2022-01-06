# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import signals
import xlsxwriter
import os, csv, json
from collections import OrderedDict
class NewSpiderPipeline(object):

    data_by_cat = {}
    file_count_by_cat = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline


    def spider_opened(self, spider):
        pass

    def spider_closed(self, spider):
        for cat_title in self.data_by_cat.keys():
            if len(self.data_by_cat[cat_title]) != 100:
                self.file_count_by_cat[cat_title] += 1
                with open('output/theconversation_com_republish({})_{}.json'.format(cat_title, str(self.file_count_by_cat[cat_title])), 'w') as outfile:
                    json.dump(self.data_by_cat[cat_title], outfile, indent=4, sort_keys=True)
                    self.data_by_cat[cat_title] = []

                print('Created new file : ' + 'theconversation_com_republish({})_{}.json'.format(cat_title, str(self.file_count_by_cat[cat_title])))

    def process_item(self, item, spider):
        if spider.custom_output:
            data_item = item['item']
            cat_title = item['cat_title']

            if cat_title not in self.data_by_cat.keys():
                self.data_by_cat[cat_title] = []
                self.file_count_by_cat[cat_title] = 0

            self.data_by_cat[cat_title].append(data_item)

            for cat_title in self.data_by_cat.keys():
                if len(self.data_by_cat[cat_title]) == 100:
                    self.file_count_by_cat[cat_title] += 1
                    with open('output/theconversation_com_republish({})_{}.json'.format(cat_title, str(self.file_count_by_cat[cat_title])), 'w') as outfile:
                        json.dump(self.data_by_cat[cat_title], outfile, indent=4, sort_keys=True)
                        self.data_by_cat[cat_title] = []

                    print('Created new file : ' + 'theconversation_com_republish({})_{}.json'.format(cat_title, str(self.file_count_by_cat[cat_title])))
            return data_item
        else:
            return item
