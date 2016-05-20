#!/usr/bin/python3

import os
import sys
import re

r = re.compile("(?P<left>\# Copyright \(C\) )(?P<years>(\d\d\d\d,\s)*(\d\d\d\d))(?P<right>\s+Tom Cato Amundsen)")


def do_file(filename):
    for enc in ('utf-8', 'iso-8859-1'):
        try:
            f = open(filename, 'r', encoding=enc)
            s = f.read()
        except UnicodeDecodeError:
            s = None
            f.close()
        if s:
            break
    if not s:
        print("failed file:", filename)
    m = r.search(s)

    def func(r):
        years = r.group('years')
        if '2016' not in years:
            years = "%s, 2016" % years
        return r.group('left') + years + r.group('right')
    s2 = r.sub(func, s)
    if s2 != s:
        with open(filename, 'w', encoding=enc) as f:
            f.write(s2)


for root, dirs, files in os.walk("."):
    if root in ('./mylint-tmpdir', './build-branch', './manual-po-tmp'):
        continue
    if root.startswith("./.git"):
        continue
    for f in files:
        if ((f.endswith(".py") or f == 'Makefile')
            or root == './exercises/standard/lesson-files'):
                    do_file(os.path.join(root, f))
