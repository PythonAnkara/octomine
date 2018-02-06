
from urllib.parse import urlparse
from pyquery import PyQuery as pq
from .worker import ThreadPool
from os.path import expanduser
import itertools
import datetime
import getpass
import shelve
import json
import time
import sys
import re
import os

class Indexer():
    """ Indexer methods """
    def __init__(self, domain, crawlerid=None):
        super(Indexer, self).__init__()
        self._this_dir, self._this_filename = os.path.split(__file__)
        self._tmp_data_folder = "%s/tmp/" % self._this_dir
        self._main_data_folder = "%s/data/" % self._this_dir
        if not os.path.isdir(self._tmp_data_folder):
            os.makedirs(self._tmp_data_folder)
        if not os.path.isdir(self._main_data_folder):
            os.makedirs(self._main_data_folder)
        self._domain = domain
        self._crawlerid = crawlerid

    def _mapper(self, words_combination):
        """ get mapper rule """
        ret = []
        for wr in words_combination:
            words, wcount, multiple = wr
            for word in words:
                if str.join(" ", word).strip() != "":
                    ret.append('%s\t%d\t%d\t%f' % (str.join(" ", word), 1, wcount, multiple))
        ret.sort(key=lambda x:(not x.islower(), x))
        return ret

    def _reducer(self, maplist):
        """ get reduced and counted values """
        current_word = None
        current_count = 0
        word = None
        for line in maplist:
            line = line.strip()
            word, count, wcount, keypoint = line.split('\t', 3)
            try:
                count = int(count)
            except ValueError:
                continue

            if current_word == word:
                current_count += count
            else:
                if current_word:
                    rpoint = ((float(current_count) / float(wcount)) * float(keypoint))
                    if current_count > 1:
                        yield '{0}\t{1}\t{2}\t{3:.8f}'.format(current_word, current_count, wcount, rpoint)
                current_count = count
                current_word = word
        if current_word == word:
            rpoint = ((float(current_count) / float(wcount)) * float(keypoint))
            if current_count > 1:
                yield '{0}\t{1}\t{2}\t{3:.8f}'.format(current_word, current_count, wcount, rpoint)

    def _setDataToMemFile(self, dkey, dvalue, dfilename):
        data_path = os.path.join(self._tmp_data_folder, "%s" % dfilename)
        fl = shelve.open(data_path)
        fl[dkey] = dvalue
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

    def _writetoFlush(self, text):
        sys.stdout.write("\r" + text)
        sys.stdout.flush()

    def _saveIndexDataToFile(self, data, domain, floor, crawlid):
        filename = "%s/index_results" % self._main_data_folder
        fl = shelve.open(filename)
        try:
            c_data = len(data)
            cs_data = 1
            p_total = 0.0
            for j in data:
                sdatalist, url = j
                wtext = "Saving index data: %{0:.0f}".format(p_total)
                self._writetoFlush(wtext)
                for i in sdatalist:
                    i_word, i_word_count, i_total_count, i_point = i.split('\t')
                    if i_word in fl.keys():
                        ls = fl[i_word]
                        ls.append((url, domain, float(i_point), datetime.datetime.now()))
                        ls.sort(key=lambda tup: tup[1])
                        ls.reverse()
                        fl[i_word] = ls.copy()
                    else:
                        fl.setdefault(i_word, [(url, domain, float(i_point), datetime.datetime.now())])
                p_total = (cs_data / c_data) * 100
                debug = "10"
                cs_data += 1

            print("\nSaving index data: Done")
        except Exception as e:
            print("save index error: %s" % str(e))
        fl.close()


    def _clearSpecialChars(self, txt):
        schars = ['!','"','#','$','%', '&', '\\', "'", '(', ')', '*', '+',
        ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^',
        '_', '`', '{', '|', '}', '~', '\t', '\n', '\r', '\x0b', '\x0c', '’', '`']
        ret = ""
        for c in schars:
            if c in txt: txt = txt.replace(c, '')
        for w in txt.split(' '):
            if w.strip() != '':
                ret += w.strip() + " "
        return ret.strip()

    def _getWordsCombination(self, textline, multiple):
        wlist = textline.strip().split(" ")
        ret = []
        for k in range(0, len(wlist), 1):
            if k == 5: break
            pr = list(itertools.permutations(wlist, (k+1)))
            ret.append((pr, len(pr), multiple))
        return ret

    def _getParseDataFromUrl(self, url):
        urlpattern = urlparse(url.lower())
        if urlpattern.path.strip() == '/': return []
        urltxt = ""
        for i in urlpattern.path.split('/'):
            if i.strip() != "" and i.count('-') > 0: urltxt = i.strip()
        if urltxt == "": return []
        txt = urltxt.replace("-", " ")
        return list(self._getWordsCombination(txt, 0.15))

    def _getParseDataFromText(self, txt, keypoint):
        word_cmb_list = []
        clist = ('#-#', '.', ',')
        ret = []
        for c in clist:
            if len(txt.split(c)) <= 1: continue
            for c1 in txt.lower().split(c):
                if c1.strip() == "": break
                if len(c1.split(' ')) > 6: c1 = ' '.join(c1.split(' ')[:5]).strip()
                tx = self._clearSpecialChars(c1.strip())
                ret.extend(self._getWordsCombination(tx, keypoint))
            break
        if len(word_cmb_list) == 0:
            if len(txt.split(' ')) > 6: txt = ' '.join(txt.split(' ')[:5]).strip()
            tx = self._clearSpecialChars(txt.lower().strip())
            ret.extend(self._getWordsCombination(tx, keypoint))
        return ret

    def _getUrlCmb(self, url):
        urlpattern = urlparse(url.lower())
        if urlpattern.path.strip() == '/': return []
        urltxt = ""
        for i in urlpattern.path.split('/'):
            if i.strip() != "" and i.count('-') > 0: urltxt = i.strip()
        if urltxt == "": return []
        txt = urltxt.replace("-", " ")
        return self._getParseDataFromText(txt, 0.40)

    def _getTitleCmb(self, title):
        return self._getParseDataFromText(title, 0.20)

    def _getHeadersCmd(self, htmldata):
        htext = ""
        for i in range(1, 7):
            for h in htmldata('h' + str(i)):
                if pq(h).text().strip() != "":
                    htext += "%s#-#" %  self._clearSpecialChars(pq(h).text().strip())
        return self._getParseDataFromText(htext, 0.15)

    def _getHyperlinkCmb(self, htmldata):
        htext = ""
        for h in htmldata('a'):
            if pq(h).text().strip() != "":
                htext += "%s#-#" %  self._clearSpecialChars(pq(h).text().strip())
        if htext.strip() == "": return []
        return self._getParseDataFromText(htext, 0.10)

    def _getDescriptionCmb(self, description):
        return self._getParseDataFromText(description, 0.18)

    def _getKeywordsCmb(self, keywords):
        if type(keywords) is not str: return []
        return self._getParseDataFromText(keywords, 0.07)

    def workToIndex(self, urldata, is_return=True, floor=0):
        try:
            wcmb = []
            pqcontent = pq(urldata['html'])
            wcmb.extend(self._getUrlCmb(urldata['url']))
            wcmb.extend(self._getTitleCmb(urldata['title']))
            wcmb.extend(self._getHeadersCmd(pqcontent))
            #wcmb.extend(self._getHyperlinkCmb(pqcontent))
            wcmb.extend(self._getDescriptionCmb(urldata['description']))
            wcmb.extend(self._getKeywordsCmb(urldata['keywords']))
            if is_return: return list(self._reducer(self._mapper(wcmb)))
            self._sdata.append((list(self._reducer(self._mapper(wcmb))), urldata['url']))
            print("%s is done" % urldata['url'])
        except Exception as e:
            print("worktoindex error: %s" % str(e))

    def _workWithWorker(self, workerid, floorid):
        while True:
            if len(self._idata) == 0: break
            urldata = self._idata.pop()
            self.workToIndex(urldata, is_return=False, floor=floorid)

    def _getTmpFileList(self, crawlerid):
        files = [f for f in os.listdir(self._tmp_data_folder) if os.path.isfile(os.path.join(self._tmp_data_folder, f))]
        for i in files:
            if i[:len(str(crawlerid))] == str(crawlerid):
                yield i

    def doIndexing(self):
        files = self._getTmpFileList(self._crawlerid)
        if files is None: return
        for i in files:
            filename = i
            domain = i.split("_")[1]
            floorid = int(i.split("_")[2])
            data_path = os.path.join(self._tmp_data_folder, "%s" % filename)
            self._idata = []
            self._sdata = []
            if os.path.isfile(data_path):
                self._idata = list(self._getDataFromMemFile("crawl_results", filename))
                os.remove(data_path)
            else: continue
            tpool = ThreadPool(1)
            for j in range(5):
                tpool.add_task(self._workWithWorker, j, floorid)
                time.sleep(1)
            tpool.wait_completion()
            self._saveIndexDataToFile(self._sdata, domain, floorid, self._crawlerid)
