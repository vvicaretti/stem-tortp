#!/bin/bash

# Create a source distribution (tarball, zip file, etc.)
python setup.py sdist

# Creates Debian source package from Python package
cd dist
py2dsc -m 'paskao <paskao@hacari.org>' tortp-1.0.tar.gz

# Configure build
cd deb_dist/tortp-1.0
echo 'tortp.egg-info/*' > debian/clean
sed -i 's/source package automatically created by stdeb 0.6.0+git/Initial release. Closes: 1.0/' debian/changelog

# Building
debuild

# Coping deb package in main directory
cd ../../../
cp dist/deb_dist/python-tortp_1.0-1_all.deb .
