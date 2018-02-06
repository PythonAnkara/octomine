
import shelve
import datetime
import os

class SearchResult(object):
    """ result returner """
    def __init__(self, title, description, url, language, domain, created_at):
        super(SearchResult, self).__init__()
        self._this_dir, self._this_filename = os.path.split(__file__)
        self._main_data_folder = "%s/data/" % self._this_dir

        self.title = title
        self.description = description
        self.url = url
        self.language = language
        self.domain = domain
        self.created_at = created_at



class Search(object):
    """Octomine searching library"""
    def __init__(self):
        super(Search, self).__init__()
        self.skip = 0
        self.limit = 10
        self.result_all_count = 0
        self.query = ""
        self.result = ()
        self.query_time = 0.0
        self._this_dir, self._this_filename = os.path.split(__file__)
        self._main_data_folder = "%s/data/" % self._this_dir
        filename = os.path.join(self._main_data_folder, "index_results")
        print(filename)
        self._conn = shelve.open(filename)
        if not os.path.isdir(self._main_data_folder):
            os.makedirs(self._main_data_folder)

    def _returnSearchResult(self):
        mlimit = self.skip + self.limit
        if mlimit > self.result_all_count:
            mlimit = self.result_all_count
        ret = ()
        for r in self.result:
            udata = self._getUrlDetail(r[0], r[1])
            ret += (SearchResult(
            udata['title'],
            udata['description'],
            udata['url'],
            udata['language'],
            udata['domain'],
            r[3]),)
        return ret

    def _getUrlDetail(self, url, domain):
        data_path = os.path.join(self._main_data_folder, "domains", domain)
        fl = shelve.open(data_path)
        dt = fl[url]
        ret = {
            'url': dt['url'],
            'title': dt['title'],
            'description': dt['description'],
            'language': dt['language'],
            'domain': dt['domain']
        }
        fl.close()
        return ret

    def search(self, q, qlimit=10, qskip=0):
        try:
            start_time = datetime.datetime.now()
            res = self._conn[q]
            rescount = len(res)
            end_time = datetime.datetime.now()
            self._conn.close()
            ftime = end_time - start_time
            ttime = ftime.seconds + ftime.microseconds / 1000000.0

            self.query = q
            self.result = res[qskip:][:qlimit]
            self.limit = qlimit
            self.skip = qskip
            self.result_all_count = rescount
            self.query_time = ttime

            return self._returnSearchResult()
        except Exception as e:
            print("can not any result for '%s' : 0" % q)
            return ()

    def __str__(self):
        mlimit = self.skip + self.limit
        if mlimit > self.result_all_count:
            mlimit = self.result_all_count
        print("About %d results for '%s'(%d-%d) listed (%f seconds)" % (self.result_all_count,
            self.query, self.skip, mlimit, self.query_time))
        print("---------------------------------------------------------------")
        for r in self.result:
            udata = self._getUrlDetail(r[0], r[1])
            print("%s\n\r(%s)" % (udata['title'], udata['url']))
            print("___")
        return ""
