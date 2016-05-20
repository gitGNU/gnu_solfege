# GNU Solfege - free ear training software
# Copyright (C) 2008, 2011, 2016  Tom Cato Amundsen
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


import os
import re
import sys

from solfege import buildinfo
from solfege import filesystem


def win32_put_langenviron(lang):
    """
    Write the filesystem.app_data()/langenviron.txt file.
    win32 only.
    """
    langfile = open(os.path.join(filesystem.app_data(), "langenviron.txt"), 'w')
    print("# rem Created by GNU Solfege %s" % buildinfo.VERSION_STRING, file=langfile)
    if lang:
        print(lang, file=langfile)
    else:
        print("# System default language. Not setting variable.", file=langfile)
    langfile.close()


def win32_get_langenviron():
    """
    Return the language defined in filesystem.app_data()/langenviron.bat
    win32 only
    """
    assert sys.platform == 'win32'
    fn = os.path.join(filesystem.app_data(), "langenviron.txt")
    lang = None
    if os.path.isfile(fn):
        try:
            for line in open(fn, 'r').readlines():
                if not line.startswith("#"):
                    lang = line.strip()
        except IOError as e:
            # Try here too, just to be sure no unicode shit bothers us.

            try:
                print("IOError reading %s:" % fn, e)
            except Exception:
                pass
    else:
        lang = _pre_3_11_win32_get_langenviron()
    if lang:
        return lang
    else:
        return "system default"


def _pre_3_11_win32_get_langenviron():
    """
    Old version of win32_get_langenviron.
    Return the language defined in filesystem.app_data()/langenviron.bat
    Return None if no language is defined or the file does not exist.
    win32 only
    """
    assert sys.platform == 'win32'
    s = ""
    try:
        langfile = open(os.path.join(filesystem.app_data(), "langenviron.bat"), 'r')
        s = langfile.read()
        langfile.close()
    except IOError:
        # we get here for example when the file does not exist
        return None
    if s:
        r = re.compile("set LANGUAGE=(?P<lang>.*)")
        for line in s.split("\n"):
            m = r.match(line)
            if m:
                return m.groups()[0]
    return None
