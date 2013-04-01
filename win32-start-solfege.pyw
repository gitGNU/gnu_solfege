import os
import sys
from subprocess import Popen

sys.path.append("../share/solfege")
from solfege import winlang

lang = winlang.win32_get_langenviron()
if lang and (lang != 'system default'):
    os.environ['LANGUAGE'] = lang

prefix =  os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0]
Popen([os.path.join(prefix, "pythonw.exe"), "solfege"] + sys.argv[1:])
