#!/bin/bash

echo "Warning: last checked in revision is exported"
version=`cat src/tpfancod/build.py | grep "version = " | sed  -e "s/version = \"\(.*\)\"/\1/"`
bzr export ../packages/tarballs/tpfancod-${version}.tar.gz
cd ../packages/tarballs
ln -sf tpfancod-${version}.tar.gz tpfancod_${version}.orig.tar.gz

