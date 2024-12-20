#!/bin/sh

cd meta

# auto update version
old_version=$(grep 'Version:' control)
new_version=$(date +"%Y_%m_%d")
sed -i "s/$old_version/Version: $new_version/g" control

chmod +x postrm
version=$(grep Version control|cut -d " " -f 2)
package=$(grep Package control|cut -d " " -f 2)
mkdir -p usr/lib/enigma2/python/Plugins/Extensions/PiconsMissing
cp -r ../src/* usr/lib/enigma2/python/Plugins/Extensions/PiconsMissing
tar -cvzf data.tar.gz usr
tar -cvzf control.tar.gz control postrm

# make sure there is not an old version
rm -f ../${package}_${version}_all.ipk

# create new ipk
ar -r ../${package}_${version}_all.ipk debian-binary control.tar.gz data.tar.gz

# clean up
rm -fr control.tar.gz data.tar.gz usr
