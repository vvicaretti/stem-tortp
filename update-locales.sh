#!/bin/bash

# Update .po files
find locale -name "*.po" -execdir xgettext -L Python -j -o tortp-gtk.po --package-name tortp-gtk --package-version 1.1 --msgid-bugs-address paskao@hacari.org --no-location `pwd`/tortp-gtk \;
find locale -name "*.po" -execdir msgfmt tortp-gtk.po -o tortp-gtk.mo \;

