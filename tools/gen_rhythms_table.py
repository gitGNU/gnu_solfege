#!/usr/bin/python3

import os
import sys
# We need to do this on the build server. For some reason, it is not
# necessary on my workstation.
sys.path.insert(0, os.getcwd())

import solfege.const

img_str = """%i:<inlinemediaobject>
      <imageobject>
        <imagedata fileref="../../graphics/rhythm-%s.png" format="PNG"/>
      </imageobject>
      <textobject>
       <phrase>%s</phrase>
      </textobject>
    </inlinemediaobject>"""
f = open("help/C/rhythmtable.xml", "w")
print("<para>", file=f)
for i, r in enumerate(solfege.const.RHYTHMS):
    f.write(img_str % (i, r.replace(" ", ""), r))
    if i != len(solfege.const.RHYTHMS) - 1:
        print(", ", file=f)
print("</para>", file=f)
f.close()
