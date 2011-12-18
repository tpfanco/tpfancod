#!/bin/bash

echo "Warning: last checked in revision is exported"
version=`cat src/tpfand/build.py | grep "version = " | sed  -e "s/version = \"\(.*\)\"/\1/"`
bzr export ../packages/tarballs/tpfand-${version}.tar.gz
cd ../packages/tarballs
ln -sf tpfand-${version}.tar.gz tpfand_${version}.orig.tar.gz

