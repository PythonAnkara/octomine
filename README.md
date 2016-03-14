# OCTOMINE

## 1. What is Octomine

Octomine is open-source engine that make websites crawling, indexing and searching. The whole system is developed with original algorithms in python programming language by PyAnkara team. Octomine is also allow to searching in websites which made crawl and index. Another feature is also it is used as a python module. If you want to use crawling, indexing and searching modules in your own projects, you can import it.

## 2. How to install Octomine

**Linux-source**: sudo python setup.py install

**Virtualenv setup and configure**

Install Virtualenv to your computer.

```sh
sudo apt-get install python-virtualenv
```

Configure Virtualenv repo to Octomine

```sh
cd ~
mkdir venvs
cd venvs
virtualenv --python=python3 octomine_env
source octomine_env/bin/activate
```

**Install Octomine in virtualenv**

```sh
cd octomine
python setup.py install
```

Then you can use this package's all attribute in python or from the command line
using "octominemain -d <domainname>".

If you want to use it without virtualenv, you may receive the error. However you can solve that error with `sudo python3 setup.py install` command.

## 3. Octomine Quickstart

To run the application, you need to use some features Octomine command. They are as follows.

| Option    | Option 2          | Help                                      |
|-----------|-------------------|-------------------------------------------|
| -i        | --infile          | get domain list to crawling in file       |
| -o        | --outfile         | write result to json file                 |
| -p        | --isprint         | print result                              |
| -d        | --domain          | crawl by domain                           |
| -f        | --floorcount      | declare max floor limit for crawl         |
| -g        | --floorurllimit   | declare max floor url limit           		|
| -w        | --withindexer     | run indexer modul after crawl proccess    |
| -s        | --search          | search by query                           |
| -l        | --querylimit      | search get by limit. Default: 10          |
| -k        | --queryskip       | search get by skipping list. Default: 0   |

Example run the command:
```bash
octominemain -d pyankara.org -p
```
## 4. How does it work

Octomine is a system that works based on the domain parameters. Crawl before the domain parameters, then makes a choice indexing if  preference is given. Indexed data is stored in a single file. When making querying the results listed is read from this file. A list of domains can also be provided with a file input like single domain input parameter. Multiple domain crawl and indexing is possible.

Results if not given extra parameters, written to single file by the system by default and them can be output to json file with additional parameters.

Each domain's home page is crawled primarily. On the home page, according to the specified number of layers to the next layer links are given into their crawl. This process continues until the specified layer limit. After each links parse process, get the output values of html, links, backlinks, domain, language, pagestatus, title, description, keywords, headers, time, charset, status, statuscommand, urlcount and rule are held temporary data file.

After the crawl is complete, the temporary files of domain in the temp folder are taken by the indexer. The file of each layer is separately processed. The links of domains are indexed by scoring method according to specific standards. These are as follows specific coefficients;

| Title            	| Percentage	| Coefficient	|
|-------------------|-------------|-------------|
| url seo words     | %40   			| 0.40				|
| title             | %20   			| 0.20				|
| description       | %18   			| 0.18				|
| headers (h1,h2,…) | %15   			| 0.15				|
| keywords          | %7    			| 0.07				|

Each sentence or word combination calculated by Mep-Reduce algorithm multiplied by the coefficients and combination - link given an overall score on the relationship and saved. The rating given before looking at the frequency of the front scoring is done by the combination of text content. For example, in a content which have 100 combination if this combination in the one time, that is multiplied with 0.01 and append to Map-Reduce process.

After indexing process, occur a new node for each combination. One to many link-combination relationship is stored in this node. Search method makes a query from a combination and access link informations in the nodes.

## 5. Octomine Data Design

Url datas after 	crawl process:

```python
url_data = {
	            'url': <str>,
	            'html': <str>,
	            'links': <list>,
	            'backlinks': <list>,
	            'domain': <str>,
	            'language': <str>,
	            'pagestatus': <int>,
	            'title': <str>,
	            'description': <str>,
	            'keywords': <list>,
	            'headers': <list>,
	            'time': <float>,
	            'charset': <str>,
	            'status': <bool>,
	            'statuscommand': <str>,
	            'urlcount': <int>,
	            'rule': <bool>
	}
```

Combination datas after indexer process:

```python
cmb_data[<cmb: str>] = [
		(
			<url: str>,
			<domain: str>,
			<point: float>,
			<created_at: datetime>
		),
		(
			<url: str>,
			<domain: str>,
			<point: float>,
			<created_at: datetime>
		),
		...
	]
```

## 6. Code References

for only domain crawl

```python
from octomine.crawler import Crawler
cr = Crawler()
urllist = ['http://' + domain]
res = cr.crawl(urllist, is_lang_parse=True, floor_count=2,
        floor_url_limit=50, is_print=True)
```

for indexing

```python
from octomine.indexer import Indexer
ind = Indexer(domain, crawlerid=res) # res output of return param from crawler. it must be uuid.
ind.doIndexing()
```

for searching

```python
from octomine.search import Search
sr = Search()
# if you want to show results quickly
sr.search(q, qlimit, qskip)
print(st)
# if you want to get all params
res = sr.search(q, qlimit, qskip)
for r in res:
	print("{title} : {language} : {index_time}\n{url}\n___".format(
		    title=r.title, language=r.language, index_time=r.created_at, url=r.url))
```

## 7. Examples

Octomine can be use many alternative commands.

Crawl domain with printing.

```sh
octominemain -d <domainname> -p
```

Crawl many domains in a list with printing.

```sh
octominemain -i <input_file_path> -p
```

Crawl domain and indexing with printing.

```sh
octominemain -d <domainname> -p -w
```

Crawl domain max 3 floor (default: 2) and indexing with printing.

```sh
octominemain -d <domainname> -f 3 -p -w
```

search with limit.(default 10)

```sh
octominemain -s "<query>" -l 20
```

search with skipping and limit.(default 0)

```sh
octominemain -s "<query>" -k 20 -l 20
```

## AUTHOR

Python Ankara

email:  <info@pyankara.org>

facebook: https://facebook.com/pythonankara

twitter: https://twitter.com/python_ankara



## THANKS

Thanks to pyankara authors for creating such and amazing tool.
