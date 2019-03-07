import requests
from requests.exceptions import RequestException
import re
import json


def get_one_page(url):
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        return None
    except RequestException:
        return None

def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield{
            'index': item[0],
            'image': item[1],
            'tilte': item[2],
            'actor': item[3].strip(),
            'time': item[4].strip()[4:],
            'score': item[5]+item[6]
        }

def write_to_file(content):
    with open("top100-maoyan.txt", 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()

def main(offset):
    url = "https://maoyan.com/board/4?offset=" + str(offset)
    
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


if __name__ == "__main__":
    for i in range(10):
        main(i*10)
