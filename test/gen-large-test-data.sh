#!/bin/bash
#
# Create a volume of test files.
# Examples, 
# * create 1 test file of 1MB size
#	gen-large-test-data.sh -c 1 -s 1048576 -p mega
# * create 2 test files of 1GB size
#   gen-large-test-data.sh -c 2 -s 1073741824 - giga
#

while getopts c:s:p: flag
do
    case "${flag}" in
        c) filecount=${OPTARG};;
        s) filesize=${OPTARG};;
        p) prefix=${OPTARG};;
    esac
done

echo "count of files to generate: $filecount";
echo "size per file (Bytes): $filesize";

[[ -z "$filecount" ]] && { echo "filecount is required" ; exit 1; }
[[ -z "$filesize" ]] && { echo "filesize is required" ; exit 1; }

LARGE_DATA_PATH=`dirname "$0"`"/large-source"

while [ $filecount -gt 0 ]; do
    echo "generating data for test file: $filecount"
    basedir="${LARGE_DATA_PATH}/$filecount"
	mkdir -p "$basedir"
    bs=1024
    count=$(( $filesize/$bs ))
    dd if=/dev/urandom of="$basedir/$prefix-$filecount" bs=$bs count=$count iflag=fullblock
    ((filecount-=1))
done
echo "done generating test data of file size: $filesize bytes"
