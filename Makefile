SHELL=/usr/bin/env bash
SOURCE_PATH:=./test/source
LARGE_DATA_PATH:=${SOURCE_PATH}/large
STAGING_PATH:=/tmp/packer
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
BIN_SIZE:=160
MAX_FILE_SIZE:=80
CERTIFICATE:=stuff.gitignore/rsa/certificate.pem
PRIVATE_KEY:=stuff.gitignore/rsa/private_key.pem

help:
	echo "Packer makefile"

clean: test_clean

test: test_pack test_unpack

test_all: test_small test_medium test_large

test_small: test_pack_small test_unpack_small
test_medium: test_pack_medium test_unpack_medium
test_large: test_pack_large test_unpack_large

test_pack_small: BIN_SIZE=100
test_pack_small: MAX_FILE_SIZE=10

test_pack_medium: BIN_SIZE=100
test_pack_medium: MAX_FILE_SIZE=100

test_pack_large: BIN_SIZE=1000
test_pack_large: MAX_FILE_SIZE=500

test_pack test_pack_small test_pack_medium test_pack_large:
	@echo
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo; echo "📦📦📦📦 Test: $@ 📦📦📦📦"
	@echo "📦📦📦📦 Testing Packing. Max file size: ${MAX_FILE_SIZE} 📦📦📦📦"
	python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize $(MAX_FILE_SIZE) --key $(CERTIFICATE)
# TODO verification steps??

test_unpack test_unpack_small test_unpack_medium test_unpack_large:
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo "📦📦📦📦 Testing Unpacking. Test: $@ 📦📦📦📦"
	python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} --key $(PRIVATE_KEY)
	@echo "📦📦📦📦 Verifying test output..."
	@(diff --brief --recursive ${SOURCE_PATH} ${RESTORE_PATH} && echo "Test: $@, Result: [PASSED]") || (echo "Test: $@, Result: [FAILED]" && exit 1)

test_clean:
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*

test_init_large_data:
	@echo "🛠 creating large dataset for test, in: ${LARGE_DATA_PATH} 🛠"
	@mkdir -p ${LARGE_DATA_PATH}
	@for n in `seq -s " " -f %02g 1 3`; do \
		dd if=/dev/urandom of="${LARGE_DATA_PATH}/dummy-1G-$$n" bs=64M count=16 iflag=fullblock; \
	done

test_clean_large_data:
	@echo "🧹 cleaning up large dataset after test, from: ${LARGE_DATA_PATH} 🧹"
	@rm -rf ${LARGE_DATA_PATH}