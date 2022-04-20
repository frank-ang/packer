SHELL=/usr/bin/env bash
SOURCE_PATH:=./test/source
STAGING_PATH:=/tmp/packer
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
BIN_SIZE:=160
FILE_MAX_SIZE:=80

help:
	echo "Packer makefile"

clean: clean_test

clean_test:
	rm -rf ${STAGING_PATH}/*
	rm -rf ${CAR_PATH}/*

test: clean_test test_pack

test_pack:
	python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize ${FILE_MAX_SIZE}

test_unpack:
	rm -rf ${STAGING_PATH}/*
	python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} --binsize ${BIN_SIZE} --filemaxsize ${FILE_MAX_SIZE}
