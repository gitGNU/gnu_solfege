#!/bin/bash

DIST=winbuild
PYGI=/C/mygi
PYVER=27

setup() {
  rm $DIST -rf
  mkdir $DIST
  cp -a /C/mypython27/* $DIST/
}
trim() {
	cd $DIST
	rm -rf Doc
	rm -rf tcl
	rm -rf Tools
	rm -rf include
	rm -rf Lib/compiler
	rm -rf Lib/lib2to3
	rm -rf Lib/lib-tk
	rm -rf Lib/hotshot
	rm -rf Lib/idlelib
	rm -rf Lib/json
	rm -rf Lib/msilib
	rm -rf Lib/test
	rm -rf Lib/wsgiref
	rm -rf Lib/curses
	rm -rf Lib/unittest
	cd ..
}
copy_mygi() {
	cp -a $PYGI/py$PYVER/* $DIST/Lib/site-packages/
	cp -a $PYGI/gtk $DIST/Lib/site-packages/
}
setup
copy_mygi
trim
make DESTDIR=$DIST prefix="" install
cp solfege/soundcard/winmidi.pyd $DIST/share/solfege/solfege/soundcard
cp win32-start-solfege.pyw winbuild/bin/
cp debugsolfege.bat winbuild/bin
echo "done!"
