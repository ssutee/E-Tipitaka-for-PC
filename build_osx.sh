rm -rf build dist
rm -f config/*.fav config/history.log

ARCHFLAGS="-arch i386" arch -i386 python setup.py py2app
