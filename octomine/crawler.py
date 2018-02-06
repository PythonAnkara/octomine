# -*- coding: utf-8 -*-

from pyquery import PyQuery as pq
from urllib.parse import urlparse
from urllib.parse import urljoin
from lxml.html import clean
from .worker import ThreadPool
from langdetect import detect
from os.path import expanduser
import requests
import datetime
import shelve
import uuid
import time
import json
import re
import os

class Crawler(object):
    """Web crawling class """
    def __init__(self):
        super(Crawler, self).__init__()
        #path = os.path.dirname(self.__file__)
        self._this_dir, self._this_filename = os.path.split(__file__)
        self._tmp_data_folder = "%s/tmp/" % self._this_dir
        self._main_data_folder = "%s/data/" % self._this_dir
        if not os.path.isdir(self._tmp_data_folder):
            os.makedirs(self._tmp_data_folder)
        if not os.path.isdir(self._main_data_folder):
            os.makedirs(self._main_data_folder)
        data_path = os.path.join(self._main_data_folder, "effective_tld_names.dat")
        with open(data_path, encoding="utf-8") as tldFile:
            self._tlds = [line.strip() for line in tldFile if line[0] not in "\n"]

    def _isValidUrl(self, url):
        regex = re.compile(
            r'^https?://'  # http:// veya https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...veya ip
            r'(?::\d+)?'  # alternatif port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        val = url is not None and regex.search(url)
        if val is None:
            return True
        else:
            return False

    def _clearSlashatEnd(self, s):
        if s[-1] == '/':
            s = s[:-1]
        return s

    def _findDomain(self, url):
        try:
            urlElements = urlparse(url)[1].split('.')
            # urlElements = ["abcde","co","uk"]
            for i in range(-len(urlElements), 0):
                lastIElements = urlElements[i:]
                #    i=-3: ["abcde","co","uk"]
                #    i=-2: ["co","uk"]
                #    i=-1: ["uk"] etc

                candidate = ".".join(lastIElements) # abcde.co.uk, co.uk, uk
                wildcardCandidate = ".".join(["*"] + lastIElements[1:]) # *.co.uk, *.uk, *
                exceptionCandidate = "!" + candidate

                # match tlds:
                if (exceptionCandidate in self._tlds):
                    return ".".join(urlElements[i:])
                if (candidate in self._tlds or wildcardCandidate in self._tlds):
                    return ".".join(urlElements[i - 1:])
                    # returns "abcde.co.uk"
        except Exception as ex:
            raise

    def _isSkipping(self, url):
        """ conrol is valid to url format """
        try:
            skippingurl = url.rsplit('/', 1)[1].lower()
            ext = ""
            #urlyapi = urlparse.urlparse(url)
            #if urlyapi.query <> '': return True
            exts = ['mp3', 'mp4', 'avi', 'flv', 'pdf', 'gz', 'zip', 'rar', 'doc', 'xls', 'xlsx',
                                'docx',
                                'ppt', 'pptx', 'tgz', 'bz2', 'jpg',
                                'jpeg', 'png', 'gif', 'sig', 'txt', 'xml', 'msi', 'jar', 'exe', 'rpm', 'wma',
                                'wav',
                                'rm', 'wmv', 'swf', 'ram', 'iso', 'bin', 'm3u']
            skippingword = ['jsessionid', 'sessionid', 'session']
            ext = skippingurl.rsplit('.', 1)[1]
            if ext in exts: return True
            return False
        except Exception as ex:
            return False

    def _isDomainParse(self, domain):
        """ Compares with the target domain, the domain will not be parsed list.  """
        skiplist = self._skipdomainlist
        for i in skiplist:
            if domain == i or domain.count('.' + i) > 0:
                return True
        return False

    def _isHaveInside(self, url, exclude):
        have = False
        for j in exclude:
            if url.count(j) > 0:
                have = True
        return have

    def _getUrls(self, h, urllimit=0, urlbase=None):
        urls = []
        try:
            if type(h) != str:
                h = h.decode()
            pqcontents = pq(h)
            sa = 0
            urlps = []
            for a in pqcontents('a'):
                url = urljoin(urlbase, pq(a).attr['href'])
                if self._isValidUrl(url): continue
                if len(url) > 500: continue
                url = self._clearSlashatEnd(url)
                url = url.split('#')[0].replace("'", "")
                dmn = self._findDomain(url)
                if not self._isSkipping(
                          url) and dmn is not None and url not in urls and not self._isDomainParse(dmn):
                    urlp = urlparse(url).path
                    if not urlp in urlps: urlps.append(urlp)
                    urls.append(url)
                    sa += 1
                if urllimit != 0 and sa > urllimit:  break
            return urls
        except Exception as ex:
            return []

    def _getOwnLinks(self, url, urls, limit=100000):
        ic_urls = []
        haric = ['iletisim', 'rss', 'sitemap']
        syc = 0
        urldomain = self._findDomain(url)
        for i in urls:
            if syc == limit: break
            idomain = self._findDomain(i)
            if idomain == urldomain and i != url:
                if not self._isHaveInside(i, haric):
                    ic_urls.append(i)
            syc += 1
        ic_urls.sort(key=type(url).__len__)  # str.__len__ or unicode.__len__
        ic_urls.reverse()
        return ic_urls

    def _getBackLinks(self, urls, url):
        try:
            ret = []
            domain = self._findDomain(url)
            for i in urls:
                domaini = self._findDomain(i)
                if domaini != domain:   ret.append(i)
            return ret
        except Exception as ex:
            return []

    def _htmlDecode(self, h, charset, url=''):
        """ decode html data  """
        h_org = h
        h2 = ''
        if charset is None: charset = 'utf-8'
        charset = charset.lower()
        try:
            if charset != '':
                h2 = h.decode(charset, 'ignore')
                h2 = h2.encode("utf-8")
                h = h2
            else:
                h2 = ''
                for charset in ['utf-8', 'iso-8859-9', 'windows-1254', 'iso-8859-1']:
                    if h2 != '': break
                    try:
                        h2 = h.decode(charset)
                        h2 = h2.encode("utf-8")
                        h = h2
                    except:
                        pass
        except Exception as ex:
            h2 = ''
        if h2 == '': h = h_org
        return h

    def _getHtml(self, url, data=None):
        """ get html data from url """
        f = {'html': '', 'status': 404, 'charset': 'UTF-8'}
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
                'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
                'Accept-Charset': 'ISO-8859-9,ISO-8859-1,utf-8;q=0.7,*;q=0.7'
            }
            request = requests.get(url, timeout=5, headers=headers)
            f['charset'] = request.encoding
            #f['html'] = self._htmlDecode(request.content, f['charset'], url)
            f['html'] = request.content.decode()
            f['status'] = request.status_code
            request.close()
        except Exception as ex:
            print("error :: getHtml ...({url}) :: {error}".format(url=url, error=ex))
        finally:
            return f

    def _isValidHost(self, host):
        """ IDN compatible domain validator """
        isv = re.compile(r'^([0-9a-z][-\w]*[0-9a-z]\.)+[a-z0-9\-]{2,15}$')
        return bool(isv.match(host))

    def _isUrlParse(self, url):
        """ Verilen urlinin domaininin cekilmeyecekler listesinde olup olmadigina bakar. """
        result = False
        character = False
        cdomain = False
        domain = self._findDomain(url)
        for i in url:
            if i == '*':
                character = True
                break
        if self._isDomainParse(domain): cdomain = True
        if cdomain or character:
            result = True
        return result

    def _clearHtmlTags(self, data):
        try:
            cleaner = clean.Cleaner(
                scripts=True,
                javascript=True,
                meta=True, safe_attrs_only=True, page_structure=True, style=True, links=True,
                remove_tags=['!--...--', '!DOCTYPE', 'a', 'abbr', 'acronym', 'address', 'applet', 'area', 'b',
                             'base',
                             'basefont', 'bdo', 'big', 'blockquote',
                             'body', 'br', 'button', 'caption', 'center', 'cite', 'code', 'col', 'colgroup',
                             'dd',
                             'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em', 'fieldset',
                             'font', 'form', 'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head',
                             'hr',
                             'html', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'label',
                             'legend', 'li', 'link', 'map', 'menu', 'meta', 'noframes', 'noscript', 'object',
                             'ol',
                             'optgroup', 'option', 'p', 'param', 'pre', 'q', 's', 'samp',
                             'script', 'select', 'small', 'span', 'strike', 'strong', 'style', 'sub', 'sup',
                             'table',
                             'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'title', 'tr', 'tt', 'u', 'ul',
                             'var',
                             'xmp'])
            lasttext = ""
            if type(data) != str:
                data = data.decode()
            for i in data.splitlines():
                for j in i.strip().split(' '):
                    if j != "":
                        lasttext = lasttext + " " + j.strip()
            ret = cleaner.clean_html(lasttext)[5:][:-6]
            rets = ''
            for i in ret.split(' '):
                if i != '':
                    rets = rets + i.strip() + ' '

            return rets.strip().replace("'", "´").replace("\\n", " ")
        except Exception as ex:
            print("error :: cleanHtmlTags :: error: {error}".format(error=ex))
            return ''

    def _findLanguage(self, h):
        langs = {'tr': '0', 'en': '1', 'az': '2', 'an': '3', 'du': '4', 'fr': '5', 'br': '6', 'it': '7'}
        cleantext = self._clearHtmlTags(h)
        result = detect(cleantext)
        if result not in langs: return '9'
        return langs[result]

    def _getLanguagebyId(self, langid):
        langs = {'0': 'tr', '1': 'en', '2': 'az', '3': 'an', '4': 'du', '5': 'fr', '6': 'br', '7': 'it'}
        if langid == '': return 'other'
        if not langid in langs: return 'other'
        return langs[langid]

    def _getTitle(self, pquery):
        return self._clearHtmlTags(pquery('title').text())

    def _getKeywords(self, pquery):
        metas = pquery('meta')
        try:
            for i in metas:
                if 'name' in i.attrib:
                    if str(i.attrib['name']).lower() == 'keywords':
                        return i.attrib['content']
            return ''
        except Exception as e:
            return ''

    def _getDescription(self, pquery):
        metas = pquery('meta')
        try:
            for i in metas:
                if 'name' in i.attrib:
                    if str(i.attrib['name']).lower() == 'description':
                        return i.attrib['content']
            return ''
        except Exception as e:
            return ''

    def _getHeaders(self, pquery):
        try:
            headers = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            ret = []
            for h in headers:
                tag = pquery(h)
                if tag == None: continue
                for i in xrange(len(tag)):
                    tip = "####" + str(type(tag.eq(i).text()))
                    if len(tag.eq(i).text().split()) < 10:
                        ret.append(tag.eq(i).text())
            return ret
        except Exception as ex:
            return []

    def _isValidSeoRule(self, url):
        urlyapi = urlparse(url)
        if urlyapi.query is '': return True
        return False

    def _writetoJsonFile(self):
        jdata = json.dumps(self._ret, indent=4, sort_keys=True)
        with open(self._filepath, "a") as fl:
            fl.write(jdata)

    def _crawlProc(self, url):
        ret = {
            'url': url,
            'html': '',
            'links': [],
            'backlinks': [],
            'domain': self._findDomain(url),
            'language': '',
            'pagestatus': 401,
            'title': '',
            'description': '',
            'keywords': [],
            'headers': [],
            'time': 0.0,
            'charset': 'utf-8',
            'status': False,
            'statuscommand': '',
            'urlcount': 0,
            'rule': False
        }

        if not self._isValidHost(ret['domain']):
            ret['statuscommand'] = 'This parameter is not standart to url'
            return ret

        if self._isSkipping(url):
            ret['statuscommand'] = 'This url format is not supported'
            return ret

        if self._isUrlParse(url):
            ret['statuscommand'] = 'This url in the skipping list'
            return ret
        crawl_start_time = datetime.datetime.now()
        ghtml = self._getHtml(url)
        ret['html'] = ghtml['html']
        ret['charset'] = ghtml['charset']
        ret['pagestatus'] = ghtml['status']
        try:
            pcontent = pq(ret['html'])
        except Exception as e:
            ret['statuscommand'] = 'It can not be analized'
            return ret

        if len(ret['html']) > self._htmlcharlimit:
            ret['statuscommand'] = 'content length outside the defined limits %d' % len(ret['html'])
            return ret

        if ret['html'].strip() == '' or ret['pagestatus'] != 200:
            ret['statuscommand'] = 'url is not accesible'
            return ret

        lang = 'other'
        if self._islangparse:  lang = self._findLanguage(ret['html'])
        ret['language'] = self._getLanguagebyId(lang)

        crawl_end_time = datetime.datetime.now()
        time_diff = crawl_end_time - crawl_start_time
        ret['time'] = time_diff.seconds + time_diff.microseconds / 1000000.0

        urls = self._getUrls(ret['html'], urllimit=self._urllimit, urlbase=url)
        ret['urlcount'] = len(urls)
        if len(urls) > 0:
            ret['links'] = self._getOwnLinks(url, urls, limit=100000)
            ret['backlinks'] = self._getBackLinks(urls, url)
        ret['title'] = self._getTitle(pcontent)
        ret['keywords'] = self._getKeywords(pcontent)
        ret['description'] = self._getDescription(pcontent)
        ret['headers'] = self._getHeaders(pcontent)
        ret['status'] = True
        ret['statuscommand'] = 'Success'
        ret['rule'] = self._isValidSeoRule(url)
        if self._isprint:
            print("{url} :: {lang} :: {time}".format(url=url, lang=ret['language'], time=ret['time']))

        return ret

    def _threadCrawlWork(self, domain, floor, threadid):
        while True:
            if len(self._urllist[domain][floor]) == 0: break
            url = self._urllist[domain][floor].pop(0)
            res = self._crawlProc(url)
            self._ret[domain].append(res)
            if floor < (self._floorcount - 1):
                self._urllist[domain][floor + 1].extend(res['links'])

    def _threadWork(self, threadid):
        while True:
            if len(self._domainlist) == 0: break
            domain = self._domainlist.pop(0)
            poolcrawl = ThreadPool(5)
            floor = 0
            while True:
                self._ret[domain] = []
                for cc in range(5):
                    poolcrawl.add_task(self._threadCrawlWork, domain, floor, cc)
                poolcrawl.wait_completion()
                self._saveCrawlDataToFile(domain, floor)
                if floor == (self._floorcount - 1): break
                floor += 1
            #self._getCrawlDataFromFile(domain, crawlid)
            del self._urllist[domain]

    def _setDataToMemFile(self, dkey, dvalue, dfilename):
        data_path = os.path.join(self._tmp_data_folder, "%s" % dfilename)
        fl = shelve.open(data_path)
        fl[dkey] = dvalue
        fl.close()

    def _setDataToFile(self, domain, url, data):
        data_path = os.path.join(self._main_data_folder, "domains")
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
        fl = shelve.open(os.path.join(data_path, domain))
        fl[url] = data
        fl.close()

    def _getDataFromMemFile(self, dkey, dfilename):
        data_path = os.path.join(self._tmp_data_folder, "%s" % dfilename)
        try:
            fl = shelve.open(data_path)
            ret = fl[dkey]
            fl.close()
            return ret
        except:
            return

    def _saveCrawlDataToFile(self, domain, floor):
        self._setDataToMemFile("crawl_results", self._ret[domain], "%s_%s_%d" %
            (self._crawlid, domain, floor))
        for r in self._ret[domain]:
            self._setDataToFile(domain, r['url'], r)
        del self._ret[domain]
        self._ret[domain] = []

    def _getCrawlDataFromFile(self, domain):
        for i in range(10):
            filename = "%s_%d_%s" % (self._crawlid, i, domain)
            data_path = os.path.join(self._tmp_data_folder, "%s" % dfilename)
            if os.path.isfile(data_path):
                print(self._getDataFromMemFile("crawl_results", filename))

    def _getAttr(self, params):
        ret = {
            'skip_domain_list': [],
            'url_limit': 0,
            'html_char_limit': 1000000,
            'is_lang_parse': False,
            'floor_count': 1,
            'floor_url_limit': 200,
            'is_print': False,
            'file_path': ''
        }
        for p_key in params:
            if p_key in ret:
                ret[p_key] = params[p_key]
        return ret

    def crawl(self, urllist, **kwargs):
        """
            Run crawling daemons
            :param urllist: urls that you want to crawl. It must be list.
            :param kwargs: It can be many params.
                skip_domain_list: list,
                url_limit: int,
                html_char_limit: int,
                is_lang_parse: bool,
                floor_count: int,
                floor_url_limit: int,
                is_print: bool,
                file_path: str
        """

        attrs = self._getAttr(kwargs)
        self._skipdomainlist = attrs['skip_domain_list']
        self._urllimit = attrs['url_limit']
        self._htmlcharlimit = attrs['html_char_limit']
        self._islangparse = attrs['is_lang_parse']
        self._floorcount = attrs['floor_count']
        self._floorurllimit = attrs['floor_url_limit']
        self._isprint = attrs['is_print']
        self._filepath = attrs['file_path']
        self._ret = {}
        self._urllist = {}
        self._domainlist = []
        for urll in urllist:
            dmn = self._findDomain(urll)
            if dmn in self._urllist:
                self._urllist[dmn][0].append(urll)
            else:
                for fcc in range(self._floorcount):
                    if fcc == 0:
                        self._urllist[dmn] = [[urll]]
                        continue
                    self._urllist[dmn].append([])
                self._domainlist.append(dmn)
        num_threads = 20
        pools = ThreadPool(num_threads)
        self._crawlid = uuid.uuid4()
        for pl in range(num_threads):
            pools.add_task(self._threadWork, pl)
            time.sleep(0.2)
        pools.wait_completion()
        if self._filepath.strip() != '': self._writetoJsonFile()
        return self._crawlid
