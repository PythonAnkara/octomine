#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import warnings
import sys
import shutil, errno
import subprocess

def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

try:
    from setuptools import setup
    setuptools_available = True
except ImportError:
    from distutils.core import setup
    setuptools_available = False

try:
    # This will create an exe that needs Microsoft Visual C++ 2008
    # Redistributable Package
    import py3exe
except ImportError:
    if len(sys.argv) >= 2 and sys.argv[1] == 'py3exe':
        print("Cannot import py3exe", file=sys.stderr)
        exit(1)

py3exe_options = {
    "bundle_files": 1,
    "compressed": 1,
    "optimize": 2,
    "dist_dir": '.',
    "dll_excludes": ['w9xpopen.exe', 'crypt32.dll'],
}

py3exe_console = [{
    "script": "./octominemain.py",
    "dest_base": "octominemain",
}]

py3exe_params = {
    'console': py3exe_console,
    'options': {"py3exe": py3exe_options},
    'zipfile': None
}

if len(sys.argv) >= 2 and sys.argv[1] == 'py3exe':
    params = py3exe_params
else:
    files_spec = [
        ('etc/bash_completion.d', ['octomine.bash-completion']),
        ('share/doc/octomine', ['README.md']),
    ]
    root = os.path.dirname(os.path.abspath(__file__))
    data_files = []
    for dirname, files in files_spec:
        resfiles = []
        for fn in files:
            if not os.path.exists(fn):
                warnings.warn('Skipping file %s since it is not present. Type  make  to build all automatically generated files.' % fn)
            else:
                resfiles.append(fn)
        data_files.append((dirname, resfiles))
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    #print(_this_dir)
    #copyanything("octomine/data", "%s/octomine/data/" % _this_dir)
    params = {}
setup(
    name='octomine',
    version='0.1.7',
    description='Octomine',
    long_description="""
    Octomine is open-source engine that make websites crawling, indexing and searching. The whole system is developed with original algorithms in python programming language by PyAnkara team. Octomine is also allow to searching in websites which made crawl and index. Another feature is also it is used as a python module. If you want to use crawling, indexing and searching modules in your own projects, you can import it.
    """,
    url = 'https://github.com/PythonAnkara/octomine', # use the URL to the github repo
    download_url = 'https://github.com/PythonAnkara/octomine/blob/master/dist/octomine-0.1.7.tar.gz', # I'll explain this in a second
    author='PyAnkara',
    author_email='info@pyankara.org',
    scripts=['octominemain'],
    packages=[
        'octomine'
    ],
    install_requires=[
        'pyquery',
        'requests',
        'langdetect'
    ],
    #data_files = [('octomine/data/', ['octomine/data/effective_tld_names.dat'])],
    package_data={'octomine': ['data/*dat']},
    # Provokes warning on most systems (why?!)
    # test_suite = 'nose.collector',
    # test_requires = ['nosetest'],

    classifiers=[
        "Topic :: Multimedia :: Video",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: Public Domain",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],

    **params
)
