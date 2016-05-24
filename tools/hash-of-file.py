#!/usr/bin/python3
# GNU Solfege - free ear training software
# Copyright (C) 2009, 2011, 2016 Tom Cato Amundsen
# Licence is GPL, see file COPYING

"""
Generate sha1 hash value of a file after removing lines
starting with # and empty lines.

This used to preserve the statistics of lesson files when
doing changes to them that does not affect the statistics.

Usage:
 ./tools/hash-of-file.py filename
"""

import sys
sys.path.insert(0, ".")

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
   import __main__
   print(__main__.__doc__)
   sys.exit()
import textwrap
from solfege import i18n
i18n.setup(".")
from solfege import statistics

print()
print("\n".join(textwrap.wrap(
 "To preserve statistics, place the following in the header "
 "of %s before making changes to it:" % sys.argv[1])))
print()
print("    replaces = \"%s\"" % statistics.hash_of_lessonfile(str(sys.argv[1])))
print()
