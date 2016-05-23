# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2007, 2008, 2011, 2016  Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys

from gi.repository import Gtk

from solfege import gu


class TracebackWindow(Gtk.Dialog):

    def __init__(self, show_gtk_warnings):
        Gtk.Dialog.__init__(self)
        self.m_show_gtk_warnings = show_gtk_warnings
        self.set_default_size(630, 400)
        self.vbox.set_border_width(8)
        label = Gtk.Label(label=_("GNU Solfege message window"))
        label.set_name('Heading2')
        self.vbox.pack_start(label, False, False, 0)
        label = Gtk.Label(label=_("Please report this to the bug database or send an email to bug-solfege@gnu.org if the content of the message make you believe you have found a bug."))
        label.set_line_wrap(True)
        self.vbox.pack_start(label, False, False, 0)
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.vbox.pack_start(scrollwin, True, True, 0)
        self.g_text = Gtk.TextView()
        scrollwin.add(self.g_text)
        self.g_close = Gtk.Button(stock='gtk-close')
        self.action_area.pack_start(self.g_close, True, True, 0)
        self.g_close.connect('clicked', lambda w: self.hide())

    def write(self, txt):
        if ("DeprecationWarning:" in txt) or \
           (not self.m_show_gtk_warnings and (
            "GtkWarning" in txt
            or "PangoWarning" in txt
            or ("Python C API version mismatch" in txt and
                ("solfege_c_midi" in txt or "swig" in txt))
            )):
            return
        sys.stdout.write(txt)
        if txt.strip():
            self.show_all()
        buffer = self.g_text.get_buffer()
        buffer.insert(buffer.get_end_iter(), txt)
        self.set_focus(self.g_close)

    def flush(self, *v):
        pass

    def close(self, *v):
        pass
