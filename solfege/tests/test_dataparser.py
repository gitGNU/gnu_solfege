# vim: set fileencoding=utf-8 :
# Solfege - free ear training software
# Copyright (C) 2007, 2008, 2011 Tom Cato Amundsen
# License is GPL, see file COPYING


import unittest
import traceback
import codecs

from solfege.testlib import I18nSetup, outdir, TmpFileBase
from solfege.dataparser import *
import solfege.parsetree as pt
import os


class TestLexer(unittest.TestCase):

    def test_get_line(self):
        l = Lexer("""#comment1
#comment2
#comment3

var = 3
""", None)
        self.assertEqual(l.get_line(0), "#comment1")
        self.assertEqual(l.get_line(1), "#comment2")
        self.assertEqual(l.get_line(2), "#comment3")
        self.assertEqual(l.get_line(3), "")
        self.assertEqual(l.get_line(4), "var = 3")

    def test_scan(self):
        p = Dataparser()
        p._lexer = Lexer("\"string\" name 1.2 2 (", p)
        self.assertEqual(p._lexer.scan(STRING), "string")
        self.assertEqual(p._lexer.scan(NAME), "name")
        self.assertEqual(p._lexer.scan(FLOAT), "1.2")
        self.assertEqual(p._lexer.scan(INTEGER), "2")
        p._lexer = Lexer("1 2 3", p)
        try:
            p._lexer.scan(STRING)
        except DataparserException as e:
            self.assertEqual("(line 1): 1 2 3\n"
                              "          ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("DataparserException not raised")

    def test_unable_to_tokenize(self):
        p = Dataparser()
        try:
            p._lexer = Lexer("question { a = 3} |!", p)
        except UnableToTokenizeException as e:
            self.assertEqual("(line 1): question { a = 3} |!\n"
                              "                            ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("UnableToTokenizeException not raised")
        try:
            p._lexer = Lexer("x = 4\n"
                             "question { a = 3} |!", p)
        except UnableToTokenizeException as e:
            self.assertEqual("(line 1): x = 4\n"
                              "(line 2): question { a = 3} |!\n"
                              "                            ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("UnableToTokenizeException not raised")

    def _test_encodings_delcar_not_first(self):
        """
        FIXME: I disabled this test because people suddenly started
        to report that UnableToTokenizeException was not raised.
        """
        s = '#\n#\n#vim: set fileencoding=iso-8859-1 : \n' \
            'name = "øæå" '
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'iso-8859-1')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'r')
        s = f.read()
        f.close()
        self.assertRaises(UnableToTokenizeException,
            Lexer, s, Dataparser())

    def _test_missing_encoding_definition_iso88591(self):
        """
        FIXME: I disabled this test because people suddenly started
        to report that UnableToTokenizeException was not raised.
        We write a simple datafile in iso-8859-1 encoding, but does not
        add the encoding line. The dataparser will assume files are utf-8
        by default, and will fail to tokenize.
        """
        s = 'name = "øæå" '
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'iso-8859-1')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'r')
        s = f.read()
        f.close()
        self.assertRaises(UnableToTokenizeException,
            Lexer, s, Dataparser())

    def test_X(self):
        s = r"""
question {
   music = music("\staff \stemUp  {
   \clef violin \key d \minor \time 4/4
    c4
    }a")
}
"""
        p = Dataparser()
        p._lexer = Lexer(s, p)


class TestDataParser(TmpFileBase):
    parserclass = Dataparser

    def assertRaisedIn(self, methodname):
        t = traceback.extract_tb(sys.exc_info()[2])
        self.assertEqual(t[-1][2], methodname)

    def test_exception_statement_1(self):
        try:
            self.do_file("b")
        except DataparserSyntaxError as e:
            self.assertRaisedIn('statement')
            self.assertEqual("(line 1): b\n" +
                              "           ^",
                              e.m_nonwrapped_text)
            self.assertEqual(e.m_token, ('EOF', None, 1, 0))
        else:
            self.fail("DataparserSyntaxError not raised")

    def test_exception_statement_2(self):
        try:
            self.do_file("a)")
        except DataparserSyntaxError as e:
            self.assertRaisedIn('statement')
            self.assertEqual("(line 1): a)\n" +
                              "           ^",
                              e.m_nonwrapped_text)
            self.assertEqual(e.m_token, (')', ')', 1, 0))
        else:
            self.fail("DataparserSyntaxError not raised")

    def test_exception_statement_3(self):
        try:
            self.do_file("""#comment
  XYZ
""")
        except DataparserSyntaxError as e:
            self.assertRaisedIn('statement')
            self.assertEqual("(line 1): #comment\n" +
                              "(line 2):   XYZ\n" +
                              "(line 3): \n" +
                              "          ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("DataparserSyntaxError not raised")

    def test_exception_statement_4(self):
        try:
            self.do_file("""#comment
  A)
""")

        except DataparserSyntaxError as e:
            self.assertRaisedIn('statement')
            self.assertEqual("(line 1): #comment\n" +
                              "(line 2):   A)\n" +
                              "             ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("DataparserSyntaxError not raised")

    def test_exception_assignment(self):
        try:
            self.do_file("question = 3")
        except AssignmentToReservedWordException as e:
            self.assertRaisedIn('assignment')
            self.assertEqual("(line 1): question = 3\n" +
                              "          ^",
                              e.m_nonwrapped_text)
        else:
            self.fail("AssignmentToReservedWordException not raised")

    def test_istr_translations_in_file1(self):
        p = self.do_file("""
         foo = "foo-C"
         foo[nb] = "foo-nb"
         question {
           var = "var-C"
           var[nb] = "var-nb"
         }
        """)
        self.assertEqual(p.tree[0].right.evaluate({}, {}),
                          'foo-C')
        self.assertEqual(p.tree[1].right.evaluate({}, {}),
                          'foo-nb')
        self.assertEqual(p.tree[2][0].right.evaluate({}, {}),
                          'var-C')
        self.assertEqual(p.tree[2][1].right.evaluate({}, {}),
                          'var-nb')
        self.assertTrue(isinstance(p.tree[2][0].right.evaluate({}, {}), istr))

    def test_istr_translations_in_file_lang_before_C(self):
        """
        The Dataparser will accept setting the translated var before the
        C locale. But the lesson file interpreter will report an
        error for this.
        """
        p = self.do_file("""
           foo[no] = "foo-no"
           foo = "foo-C"
        """)
        self.assertEqual(p.tree[0].left, "foo[no]")
        self.assertEqual(p.tree[0].right.m_value, "foo-no")
        self.assertEqual(p.tree[0].right.m_value.cval, "foo-no")
        self.assertEqual(p.tree[1].right.m_value, "foo-C")

    def test_i18n_list_fails(self):
        try:
            self.do_file('foo[no] = "foo-no", "blabla" ')
        except CanOnlyTranslateStringsException as e:
            self.assertEqual(e.m_nonwrapped_text,
               '(line 1): foo[no] = "foo-no", "blabla" \n'
               + '                    ^')
        else:
            self.fail("CanOnlyTranslateStringsException not raised")

    def test_i18n_int_fails(self):
        try:
            self.do_file('foo[no] = 8')
        except CanOnlyTranslateStringsException as e:
            self.assertEqual(e.m_nonwrapped_text,
               '(line 1): foo[no] = 8\n'
               + '                    ^')
        else:
            self.fail("CanOnlyTranslateStringsException not raised")

    def test_import(self):
        p = self.do_file("\n".join([
            "import progression_elements",
            "t = progression_elements.I",
        ]))
        self.assertEqual(len(p.tree), 2)
        self.assertTrue(isinstance(p.tree[0], pt.Assignment))
        self.assertTrue(isinstance(p.tree[0].right, pt.Program))
        self.assertTrue(isinstance(p.tree[1], pt.Assignment))
        self.assertTrue(isinstance(p.tree[1].right, pt.Identifier))

    def test_import_as(self):
        p = self.do_file("\n".join([
            "import progression_elements as p",
            "t = p.I",
            "question {",
            "   prog = p.I",
            "}"]))
        self.assertEqual(len(p.tree), 3)
        self.assertTrue(isinstance(p.tree[0], pt.Assignment))
        self.assertTrue(isinstance(p.tree[0].right, pt.Program))
        self.assertTrue(isinstance(p.tree[1].right, pt.Identifier))
        self.assertTrue(isinstance(p.tree[2][0].right, pt.Identifier))

    def test_pt_2(self):
        p = self.do_file("""header {
        module = idbyname
        help = "idbyname-intonation"
        title = _("Is the interval flat, in tune or sharp? %s cent wrong") % 10
        lesson_heading = _("Just interval: %s") % _("Minor Second") + " (16:15)"
        filldir = vertic
}
        """)
        for d in p.tree[0]:
            if d.left == 'module':
                self.assertEqual(d.right, 'idbyname')

    def test_nested_block(self):
        """
        As we can see, the Dataparser class and the parsetree code
        can handle nested blocks.
        """
        p = self.do_file("question { a = 4 subbl { b = 5} }")
        self.assertTrue(isinstance(p.tree[0], pt.Block))
        self.assertTrue(isinstance(p.tree[0][0], pt.Assignment))
        self.assertTrue(isinstance(p.tree[0][1], pt.Block))
        self.assertTrue(isinstance(p.tree[0][1][0], pt.Assignment))
        self.assertEqual(p.tree[0][1][0].right.evaluate({}, {}), 5)

    def test_named_block(self):
        p = self.do_file('element I { label = "label-I" } '
                      + 'element II { label = "label-II" }')
        self.assertEqual(len(p.tree), 2)
        self.assertEqual(len(p.tree[0]), 1)
        self.assertEqual(len(p.tree[1]), 1)
        self.assertTrue(isinstance(p.tree[0], pt.NamedBlock))
        self.assertEqual(p.tree[0][0].right.evaluate({}, {}), 'label-I')
        self.assertTrue(isinstance(p.tree[1], pt.NamedBlock))
        self.assertEqual(p.tree[1][0].right.evaluate({}, {}), 'label-II')


class TestIstr(I18nSetup):

    def test_musicstr(self):
        s = istr(r"\staff{ c e g }")
        self.assertTrue(isinstance(s, str))

    def test_add_translations1(self):
        # i18n.langs: nb_NO, nb, C
        # name = "Yes"
        # name[no] = "Ja"
        s = "Yes"
        s = istr(s)
        self.assertEqual(str(s), 'Yes')
        s = s.add_translation('nb', 'Ja')
        self.assertEqual(s, 'Ja')
        s = s.add_translation('nb_NO', 'Ja!')
        self.assertEqual(s, 'Ja!')

    def test_add_translations2(self):
        # i18n.langs: nb_NO, nb, C
        # name = "Yes"
        # name[no] = "Ja"
        s = "Yes"
        s = istr(s)
        self.assertEqual(s, 'Yes')
        s = s.add_translation('nb_NO', 'Ja!')
        self.assertEqual(s, 'Ja!')
        s = s.add_translation('nb', 'Ja')
        self.assertEqual(s, 'Ja!', "Should still be 'Ja!' because no_NO is preferred before no")

    def test_override_gettext(self):
        s = dataparser_i18n_func("major")
        self.assertEqual(s, "dur")
        self.assertEqual(s.cval, "major")
        s = s.add_translation('nb', "Dur")
        self.assertEqual(s, "Dur")

    def test_type(self):
        s = istr("jo")
        self.assertIsInstance(s, istr)
        self.assertIsInstance(s, str)


class TestEncodingSniffer(TmpFileBase):
    parserclass = Dataparser

    def test_file_not_found(self):
        self.assertRaises(FileNotFoundError, read_encoding_marker_from_file, "asdfasdf")
        self.assertEqual(
            read_encoding_marker_from_file("exercises/standard/lesson-files/progression-atte"),
            "iso-8859-1")
        self.assertEqual(
            read_encoding_marker_from_file("exercises/standard/lesson-files/chord-min-major"),
            None)

    def test_from_string(self):
        self.assertEqual(read_encoding_marker_from_string(
            "# vim: set fileencoding=findme\n"
            + "# line\n"
            + "line\n"), "findme")
        self.assertEqual(read_encoding_marker_from_string(
            "# comment\n"
            + "# vim: set fileencoding=findme\n"
            + "# line\nline\n"), "findme")
        # Test that the file encoding is only detecte if placed in one
        # of the first two lines
        self.assertEqual(read_encoding_marker_from_string(
            "line 1\n"
            + "line 2\n"
            + "# vim: set fileencoding=findme\n"
            + "# line\nline\n"), None)

    def test_utf8_in_first_line(self):
        self.assertEqual(read_encoding_marker_from_string(
            "# ソルフェージュ\n"
            + "# vim: set fileencoding=findme\n"
            + "# line\nline\n"), "findme")

    def test_empty_string(self):
        self.assertIsNone(read_encoding_marker_from_string(""))

    def test_empty_lines(self):
        self.assertIsNone(read_encoding_marker_from_string("\n\n\n"))
        self.add_file("\n\n\n\n\n\n", "empty-lines")
        self.assertIsNone(read_encoding_marker_from_file(
            os.path.join(self.tmpdir, "empty-lines")))

    def test_empty_file(self):
        self.add_file("", "empty-file")
        self.assertIsNone(read_encoding_marker_from_file(
            os.path.join(self.tmpdir, "empty-file")))

suite = unittest.makeSuite(TestLexer)
suite.addTest(unittest.makeSuite(TestDataParser))
suite.addTest(unittest.makeSuite(TestIstr))
suite.addTest(unittest.makeSuite(TestEncodingSniffer))
