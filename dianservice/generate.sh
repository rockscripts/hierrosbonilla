rm -r PKG-INFO
rm -r dist
rm -r build
python3 setup.py bdist_egg
python3 setup.py bdist_rpm
python3 setup.py install
