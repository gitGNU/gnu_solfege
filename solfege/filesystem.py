# GNU Solfege - free ear training software
# Copyright (C) 2005, 2006, 2007, 2008, 2011, 2016 Tom Cato Amundsen
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


r"""
  linux                 win 3.8                           win 3.9
    ~                   C:\D&S\User
~/.solfegerc            C:\D&S\User\.solfegerc            %APPDATA\GNU Solfege\solfegerc
~/.solfege              C:\D&S\USer\.solfege              %APPDATA%\GNU Solfege
~/.solfege/trainingsets C:\D&S\User\.solfege\trainingsets My Documents\GNU Solfege\trainingsets
~/.solfege/eartr.tests  C:\D&S\User\.solfege\eartr.tests  My Documents\GNU Solfege\eartr.tests
~/lessonfiles           C:\D&S\User\lessonfiles           My Documents\GNU Solfege\lessonfiles

MSWIN: app_data() => %APPDATA%\GNU Solfege
       rcfile() => app_data()\solfegerc
       user_data() => MyDocuments\GNU Solfege
Linux: app_data() => ~/.solfege
       rcfile() => ~/.solfegerc
       user_data() => app_data()

Example locations:
    app_data()/learningtrees
    app_data()/testresults
    app_data()/statistics

    user_data()/trainingsets
    user_data()/eartrainingtests
"""

import locale
import os
import sys
if sys.platform == 'win32':
    from solfege import mywinreg
    import winreg
# This name will be used as folder name on MS Windows, to create one
# folder in the "My Documents" folder, and one folder in "Application Data"
appname = "GNU Solfege"


def get_home_dir():
    ''' Try to find user's home directory, otherwise return current directory.'''
    path1 = os.path.expanduser("~")
    try:
        path2 = os.environ["HOME"]
    except KeyError:
        path2 = ""
    try:
        path3 = os.environ["USERPROFILE"]
    except KeyError:
        path3 = ""

    if not os.path.exists(path1):
        if not os.path.exists(path2):
            if not os.path.exists(path3):
                return os.getcwd()
            else: return path3
        else: return path2
    else: return path1


def win32_program_files_folder():
    """
    Return the name of the C:\Program files folder.
    """
    return mywinreg._get_reg_value(winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion", r"ProgramFilesDir")


# FIXME remove??
def expanduser(s):
    return s.replace("~", get_home_dir())


def user_data():
    """
    Return the full path name of a directory where solfege  by default will suggest to
    place the directories trainingsets/ eartrainingtests/
    """
    if sys.platform == "win32":
        return os.path.join(mywinreg._get_reg_user_value(mywinreg.SHELL_FOLDERS, 'Personal'), appname)
    else:
        return os.path.expanduser("~/.solfege")


def rcfile():
    """
    Return the full name of the users rc file.
    """
    if sys.platform == "win32":
        return os.path.join(mywinreg.get_appdata(), appname, "solfegerc")
    else:
        return os.path.expanduser("~/.solfegerc")


def app_data():
    """
    Return the full path name of the directory that will store files
    created by the program. For example statistics and test results.
    """
    if sys.platform == "win32":
        return os.path.join(mywinreg.get_appdata(), appname)
    else:
        return os.path.expanduser("~/.solfege")
