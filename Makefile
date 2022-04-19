SHELL=/usr/bin/env bash
STAGING_PATH:=/tmp/packer
OUTPUT_PATH:=./test/output
BIN_SIZE:=160
FILE_MAX_SIZE:=80

help:
	echo "Packer makefile"

clean_test:
	rm -rf ${STAGING_PATH}/*
	rm -rf ${OUTPUT_PATH}/*

test: clean_test test_pack

test_pack:
	python ./packer.py -p -s ./test/source -t ${STAGING_PATH} -o ${OUTPUT_PATH} -b ${BIN_SIZE} --filemaxsize ${FILE_MAX_SIZE}

test_unpack:
	echo TODO
