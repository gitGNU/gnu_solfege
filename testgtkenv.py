# GNU Solfege - free ear training
# Copyright (C) 2009, 2011, 2016 Tom Cato Amundsen

from __future__ import absolute_import
from __future__ import print_function
import sys
print(sys.version)

from gi.repository import Gtk
print(Gtk)


class Win(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_default_size(600, 400)
        b = Gtk.Button("Click to quit")
        b.connect('clicked', Gtk.main_quit)
        self.add(b)

w = Win()
w.show_all()
Gtk.main()
