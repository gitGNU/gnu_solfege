# vim: set fileencoding=utf8 :
# Solfege - free ear training software
# Copyright (C) 2007, 2008, 2011 Tom Cato Amundsen
# License is GPL, see file COPYING


import unittest
import codecs
import doctest
import os.path
from solfege.testlib import outdir

import solfege.cfg
from solfege.cfg import parse_file_into_dict
from solfege import cfg

class Test_parse_file_into_dict(unittest.TestCase):
    def test_parse_default_config(self):
        d = {}
        parse_file_into_dict(d, "default.config")
        self.assertEqual(d['gui']['expert_mode'], "false")
    def test_fail_on_non_utf8(self):
        filename = os.path.join(outdir, 'bad-unicode.ini')
        outfile = open(filename, 'w', encoding="iso-8859-1")
        outfile.write("# This file is not in utf8 encoding\n"
             "[sound]\n"
             "midi_player=/ABC/Us\xe9r\xa0\xff\xff\xff\x00r /bin/timidity\n")
        outfile.close()
        d = {}
        self.assertRaises(UnicodeDecodeError, parse_file_into_dict, d, filename)
        os.remove(filename)
    def test_parse_utf8(self):
        filename = os.path.join(outdir, 'ok-utf8.ini')
        outfile = codecs.open(filename, 'w', 'utf-8')
        outfile.write("# This file is in utf8 encoding\n"
                      "[sound]\n"
                      "s=/home/Usér/bin/prog\n"
                      "f=1.1\n"
                      "i=3\n")
        outfile.close()
        d = {}
        parse_file_into_dict(d, filename)
        self.assertEqual(d['sound']['i'], '3')
        self.assertEqual(d['sound']['f'], '1.1')
        self.assertEqual(d['sound']['s'], '/home/Us\xe9r/bin/prog')
        self.assertTrue(isinstance(d['sound']['s'], str))
        self.assertTrue(isinstance(d['sound']['s'], str))
    def test_set_str(self):
        cfg.set_string("abc/def", "str string")
        cfg.set_string("abc/ghi", "unicode string ØÆÅ")
        self.assertTrue(isinstance(cfg.get_string("abc/def"), str))
        self.assertTrue(isinstance(cfg.get_string("abc/ghi"), str))

suite = unittest.makeSuite(Test_parse_file_into_dict)
suite.addTest(doctest.DocTestSuite(solfege.cfg))
