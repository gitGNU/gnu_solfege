# Solfege - free ear training software
# Copyright (C) 2007, 2008, 2011, 2016 Tom Cato Amundsen
# License is GPL, see file COPYING


import unittest
from solfege.frontpage import *


class TestLearningTree(unittest.TestCase):

    def test_create_page(self):
        page = Page('noname')
        self.assertEqual(len(page), 0)
        self.assertEqual(page.m_name, 'noname')
        page2 = Page('noname', [Column()])
        self.assertEqual(len(page2), 1)
        Page()

    def test_column(self):
        # empty col
        col = Column()
        linklist = LinkList('Intervals', [])
        # can also construct with children
        col = Column(linklist)
        self.assertEqual(len(col), 1)

    def test_add_linklist(self):
        page = Page('noname', [Column()])
        column = page[-1]
        ll = column.add_linklist('Intervals')
        self.assertEqual(ll.m_name, 'Intervals')
        self.assertFalse(ll)

    def test_linklist(self):
        ll = LinkList('Intervals', [])
        self.assertEqual(len(ll), 0)
        ll = LinkList('Intervals', ['sdfsf23'])
        self.assertEqual(len(ll), 1)
        self.assertEqual(ll[0], 'sdfsf23')
        self.assertEqual(ll, ['sdfsf23'])
        ll.append('47d82-f32sd93-f8sd9s32')
        ll.append(Page('noname'))
        self.assertEqual(ll.m_name, 'Intervals')
        self.assertEqual(len(ll), 3)

    def test_is_empty(self):
        p = Page()
        self.assertEqual(p.is_empty(), True)
        p.append(Column())
        self.assertEqual(p.is_empty(), True)
        p[0].append(LinkList('test', []))
        self.assertEqual(p.is_empty(), True)

    def test_load_tree(self):
        load_tree("exercises/standard/learningtree.txt")

    def test_iterate_filenames(self):
        p = Page('noname', [
            Column(
                LinkList('heading', [
                    'id1', 'id2', 'id3', ]),
            ),
        ])
        self.assertEqual(list(p.iterate_filenames()),
                ['id1', 'id2', 'id3'])
        p[0].append(LinkList('heading', ['id1', 'id5']))
        self.assertEqual(list(p.iterate_filenames()),
                ['id1', 'id2', 'id3', 'id1', 'id5'])

    def test_use_count(self):
        p = Page('noname', [
            Column(
                LinkList('heading', [
                    'id1', 'id2', 'id3', ]),
            ),
        ])
        self.assertEqual(p.get_use_dict(), {'id1': 1, 'id2': 1, 'id3': 1})
        p[0].append(LinkList('heading', ['id1', 'id5']))
        self.assertEqual(p.get_use_dict(), {'id1': 2, 'id2': 1, 'id3': 1, 'id5': 1})

    def test_iterate_topics_for_file(self):
        p = Page('noname', [
            Column(
                LinkList('heading', [
                    'id1', 'id2', 'id3', ]),
            ),
        ])
        p[0].append(LinkList('heading2', ['id1', 'id5']))
        self.assertEqual(list(p.iterate_topics_for_file('id1')),
                ['heading', 'heading2'])
        self.assertEqual(list(p.iterate_topics_for_file('id3')),
                ['heading'])
        self.assertEqual(list(p.iterate_topics_for_file('id5')),
                ['heading2'])


suite = unittest.makeSuite(TestLearningTree)
