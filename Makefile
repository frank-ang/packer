SHELL=/usr/bin/env bash
SOURCE_PATH:=./test/source
STAGING_PATH:=/tmp/packer
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
BIN_SIZE:=160
MAX_FILE_SIZE:=80

help:
	echo "Packer makefile"

clean: test_clean

test: test_clean test_pack test_unpack

test_suite: test_clean test_small test_medium test_large

test_small: test_clean test_pack_small test_unpack_small
test_medium: test_clean test_pack_medium test_unpack_medium
test_large: test_clean test_pack_large test_unpack_large

test_pack_small: BIN_SIZE=100
test_pack_small: MAX_FILE_SIZE=10

test_pack_medium: BIN_SIZE=100
test_pack_medium: MAX_FILE_SIZE=100

test_pack_large: BIN_SIZE=1000
test_pack_large: MAX_FILE_SIZE=500

test_pack test_pack_small test_pack_medium test_pack_large: test_clean
	@echo; echo "📦📦📦📦 Test: $@ 📦📦📦📦"
	@echo "📦📦📦📦 Testing Packing. Max file size: ${MAX_FILE_SIZE} 📦📦📦📦"
	python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize $(MAX_FILE_SIZE)
# TODO verification steps??

test_unpack test_unpack_small test_unpack_medium test_unpack_large:
	@echo "📦📦📦📦 Testing Unpacking. Test: $@ 📦📦📦📦"
	rm -rf ${STAGING_PATH}/*
	rm -rf ${RESTORE_PATH}/*
	python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} 
	@echo "📦📦📦📦 Verifying test output..."
	@(diff --brief --recursive ${SOURCE_PATH} ${RESTORE_PATH} && echo "Test: $@, Result: [PASSED]") || (echo "Test: $@, Result: [FAILED]" && exit 1)

test_clean:
	rm -rf ${STAGING_PATH}/*
	rm -rf ${CAR_PATH}/*
	rm -rf ${RESTORE_PATH}/*
