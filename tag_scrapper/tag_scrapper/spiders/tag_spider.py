import scrapy
import os
import pandas as pd
import logging

class TagSpider(scrapy.Spider):
    name = 'tags'
    allowed_domains = ["steampowered.com"]
    def start_requests(self):
        # read urls from appids.csv
        appids = []
        bypass_age_cookies = {
            'mature_content':'1',
            'birthtime': '945730801',
            'lastagecheckage': '21-0-2000'}
        url = "https://store.steampowered.com/app/"

        try:
            appids = pd.read_csv('appids.csv', encoding='utf-8-sig')
            appids = appids['appid'].astype(str).tolist()
        except FileNotFoundError:
            print("appids.csv not found. Make sure it's in this directory: " + os.getcwd())
            return
        
        for appid in appids:
            yield scrapy.Request(url=url + appid, cookies=bypass_age_cookies, callback=self.parse_tags)

    def parse_tags(self, response):
        if '/agecheck/app' in response.url:
            g_sessionid = response.xpath('//script[contains(text(), "g_sessionID")]/text()').extract_first().split('"')[1]
            yield scrapy.FormRequest(
                url='https://store.steampowered.com/agecheckset/' + "app" + "/" + response.url.split('/')[4],
                method='POST',
                formdata={ 
                    'sessionid': g_sessionid,
                    'ageDay': '21',
                    'ageMonth': '2',
                    'ageYear': '2000'
                },
                callback=self.parse_tags
            )
        else:
            yield {
                'appid': response.url.split('/')[4],
                'name': response.css('div.apphub_AppName::text').extract_first(), # useful for debugging
                'tags': [tag.strip() for tag in response.css('a.app_tag::text').extract() if tag != '+']
            }