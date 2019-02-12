from urllib.parse import quote_plus

import hashlib
import requests
from bs4 import BeautifulSoup

from socialapis.translate import get_sentiment_info


class NewsRequest(object):

    def __init__(self, url, regional, news_source, lang):
        self.url = url
        self.regional = regional
        self.news_source = news_source
        self.lang = lang


from queue import Queue
from threading import Thread

urls = [
    {
        'url': 'https://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&q={query}&csed=in&csep=false&sort=rated&output=rss&num={limit}&scoring=d&q_epo={query}',
        'regional': False, 'news_source': 'google', 'lang': 'english'},
]


def checkKeyword(keyword, content):
    for word in content.lower().split():
        if word.rfind('\'') > 0:
            word = word.split('\'', 1)[0]
        if word.rfind('\"') > 0:
            word = word.split('\"', 1)[0]
        if word.strip() == keyword.lower():
            return True
    else:
        return False


class NewsApi(object):

    def __init__(self):
        self.q = Queue(len(urls) * 2)
        self.session = requests.Session()

    def doWork(self):
        while True:
            request = self.q.get()
            try:
                response = self.session.get(url=request.url)
                self.doSomethingWithResult(response, request)
            except Exception as e:
                print(e)
                pass
            self.q.task_done()

    def doSomethingWithResult(self, response, request: NewsRequest):

        if response:
            content = BeautifulSoup(response.text, 'html.parser')

            if request.news_source == 'google':
                items = content.find_all('item')
                items = items[1:] if items and len(items) > 0 else []
                for d in items:
                    title = d.title.get_text()
                    descriptionTag = BeautifulSoup(d.description.get_text(), 'html.parser')
                    description = descriptionTag.text
                    link = descriptionTag.find('a')['href']
                    pubdate = d.pubdate.get_text()
                    source = d.contents[-1].__str__()
                    image = None
                    if bool(BeautifulSoup(source, "html.parser").find()):
                        if source.rfind('media') != -1:
                            media = BeautifulSoup(source, "html.parser").find('media:content')
                            if media:
                                image = media['url']
                            source = None

                    # polarity = None
                    sentiment, confidence = get_sentiment_info(description)
                    polarity = {'key': sentiment, 'value': confidence}
                    self.news.append(
                        {
                            'newsid': hashlib.md5(title.lower().encode('utf-8')).hexdigest(),
                            'link': link,
                            'title': title,
                            'titleParsed': title,
                            'image': image,
                            'section': 'nation',
                            'description': description,
                            'descriptionParsed': description,
                            'created_at': pubdate,
                            'source': source,
                            'regional': False,
                            'polarity': polarity

                        })

    def getnews(self, keyword=None, limit=10):

        self.news = list()
        self.keyword = keyword.lower()

        for i in range(len(urls)):
            t = Thread(target=self.doWork)
            t.daemon = True
            t.start()

        for url in urls:
            request = NewsRequest(**url)
            request.keyword = self.keyword
            if request.news_source == 'google':
                url = request.url.format(query=quote_plus(self.keyword), limit=limit)
                request.url = url
            self.q.put(request)

        self.q.join()

        return self.news


news = NewsApi()

if __name__ == '__main__':
    data = news.getnews('pawankalyan', limit=5)
    for d in data:
        print(d)
