# Setup build environment
set -e

if [ ! -f "solfege/solfege.py" ]; then
	echo "Run from the directory below script location."
	exit 10
fi

DEPS="deps-dl"
PYVER="2.7.5"
PYTHONMSI="python-$PYVER.msi"
PYGI="pygi-aio-3.4.2rev11.7z"
PYGIn7="pygi-aio-3.4.2rev11"

ENVDIR="mypython"

if [ ! -d "$DEPS" ]; then
  # Control will enter here if $DIRECTORY doesn't exist.
  mkdir $DEPS
fi

if [ -f "$DEPS/$PYTHONMSI" ]; then
  echo "Python found."
else
  wget http://www.python.org/ftp/python/$PYVER/python-$PYVER.msi -O "$DEPS/$PYTHONMSI"
fi

if [ -f "$DEPS/$PYGI" ]; then
  echo "Pygi-aio found."
else
  wget https://osspack32.googlecode.com/files/$PYGI -O "$DEPS/$PYGI" --no-check-certificate 
fi

if [ ! -d "$DEPS/$PYGIn7" ]; then
  echo "Please unpack $PYGI to $DEPS/$PYGIn7/"
  exit 10
else
  echo "$DEPS/$PYGIn7/ is unpacked"
fi

echo "Recreating $ENVDIR"
rm -rf $ENVDIR
mkdir $ENVDIR

DD=`pwd`
PDIR="C:\\MinGW\\msys\\1.0\\home\\"$(basename "$DD")"\\mypython"
echo msiexec /a "$DEPS\\$PYTHONMSI" TARGETDIR="\"$PDIR\""  > installpython.bat
cmd /c installpython
#rm installpython.bat
cp -a deps-dl/pygi-aio-3.4.2rev11/py27/* mypython/lib/site-packages/
cp -a deps-dl/pygi-aio-3.4.2rev11/gtk mypython/lib/site-packages/
