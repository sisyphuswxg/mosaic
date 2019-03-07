from urllib.parse import urlencode
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from hashlib import md5
from multiprocessing import Pool
from config import *
import requests
import json
import random
import re
import os
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def get_page_index(offset, keyword):
    # headers
    data = {
        'aid': 24, 
        'app_name': 'web_serarch',
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'en_qc': 1,
        'cur_tab': 1,
        'from': 'search_tab',
        'pd': 'synthesis'
    }

    url = 'https://www.toutiao.com/api/search/content/?' + urlencode(data)
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        return None
    except RequestException:
        print("请求索引页错误")
        return None

def get_page_detail(url):

    headers=[
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'},
        {'User-Agent':'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;'},
        {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'},
        {'User-Agent':'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'}
    ]

    try:
        resp = requests.get(url, headers=random.choice(headers))
        if resp.status_code == 200:
            return resp.text
        return None
    except RequestException:
        print("请求详情页出错")
        return None 

def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            if item.get('article_url') != None:
                yield item.get('article_url')

def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    rets = re.findall('http://p(.*?)&quot;', html, re.S)
    images = ['http://p' + ret for ret in rets]
    for image in images:
        if image:
            download_image(image)
    return {
        "title": title,
        "url": url,
        "images": images
    }

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print("存储到MongoDB成功", result)
        return True
    return False

def download_image(url):
    print("正在下载: ", url)
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            save_image(resp.content)
        return None
    except RequestException:
        print("请求图片出错")
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_index(offset, KEYWORD)
    for url in parse_page_index(html):
        print(url)
        detail_html = get_page_detail(url) 
        if detail_html:
            ret = parse_page_detail(detail_html, url)
            if ret["images"]:
                save_to_mongo(ret)


if __name__ == "__main__":
    pool = Pool()
    pool.map(main, [x * 20 for x in range(GROUP_START, GROUP_END * 1)])


