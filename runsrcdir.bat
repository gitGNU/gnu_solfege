rem GNU Solfege - free eartraining
rem Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2013  Tom Cato Amundsen

rem The contents of langenviron.bat is set by configwindow.py
rem and is used to select the language to use.

rem For this script to work, you must setup things as described
rem in INSTALL.win32

IF EXIST "%APPDATA%\GNU Solfege\langenviron.bat" (call "%APPDATA%\GNU Solfege\langenviron.bat")

rem set PATH=..\mypython\Lib\site-packages\gtk
set PATH=win32\python\Lib\site-packages\gtk

win32\python\python.exe solfege.py
rem ..\mypython\python.exe solfege.py
pause
