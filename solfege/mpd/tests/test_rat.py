# Solfege - free ear training software
# Copyright (C) 2007, 2008, 2011, 2016 Tom Cato Amundsen
# License is GPL, see file COPYING

import unittest

from solfege.mpd.rat import Rat


class TestRat(unittest.TestCase):

    def test_constructor(self):
        self.assertEqual(float(Rat(1, 4)), 0.25)
        self.assertEqual(float(Rat(9, 8)), 1.125)
        self.assertEqual(float(Rat(4, 4)), 1.0)
        # I was a little surprised by the following, that 4/4 is not
        # simplified to 1, but I also see that we need it this way
        # for time signatures.
        r = Rat(4, 4)
        self.assertEqual(float(r), 1.0)
        self.assertEqual(r.m_num, 4)
        self.assertEqual(r.m_den, 4)

    def test_as_float(self):
        self.assertEqual(float(Rat(1, 2)), 0.5)
        self.assertEqual(float(Rat(2, 4)), 0.5)

    def test_addition(self):
        self.assertEqual(Rat(1, 4) + Rat(1, 4), Rat(2, 4))
        self.assertEqual(Rat(3, 4) + Rat(1, 4), Rat(1, 1))
        self.assertEqual(Rat(3, 4) + Rat(1, 4), Rat(2, 2))
        self.assertEqual(Rat(4, 4) + Rat(1, 4), Rat(5, 4))

    def test_subtract(self):
        self.assertEqual(Rat(3, 4) - Rat(1, 4), Rat(1, 2))

    def test_division(self):
        self.assertEqual(Rat(1, 2) / Rat(1, 2), Rat(1, 1))
        self.assertEqual(Rat(1, 2) / Rat(2, 4), Rat(1, 1))
        self.assertEqual(Rat(1, 4) / 2, Rat(1, 8))
        self.assertEqual(Rat(1, 4) / Rat(3, 2), Rat(1, 6))
        self.assertEqual(Rat(1, 4) / 2, Rat(1, 8))

    def test_cmp(self):
        self.assertNotEqual(Rat(4, 3), None)
        self.assertEqual(Rat(1, 2), Rat(2, 4))
        self.assertTrue(True)

    def test_listsort(self):
        v = [Rat(0, 4), Rat(3, 8), Rat(1, 8), Rat(1, 4)]
        self.assertEqual(v, [Rat(0, 4), Rat(3, 8), Rat(1, 8), Rat(1, 4)])
        v.sort()
        self.assertEqual(v, [Rat(0, 4), Rat(1, 8), Rat(1, 4), Rat(3, 8)])


suite = unittest.makeSuite(TestRat)
