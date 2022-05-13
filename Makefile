SHELL=/bin/bash
SOURCE_PATH:=./test/source
LARGE_DATA_PATH:=./test/large-source
#STAGING_PATH:=/tmp/packer
STAGING_PATH:=./test/staging
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
# Bin Size and Max Filesize (both should be set to identical values) in Bytes
#  For 32GB Sector size, the usable size should be 34,091,302,912 bytes
#  https://lotus.filecoin.io/tutorials/lotus/large-files/
# TODO Verify what should be the optimum value. Test with 34091302912
BIN_SIZE:=32000000000
MAX_FILE_SIZE:=32000000000
#CERTIFICATE_ROOT:=stuff.gitignore/rsa
CERTIFICATE_ROOT:=./test/security.rsa.gitignore
CERTIFICATE:=${CERTIFICATE_ROOT}/certificate.pem
PRIVATE_KEY:=${CERTIFICATE_ROOT}/private_key.pem

help:
	echo "Packer makefile"

clean: test_clean

test: test_pack test_unpack

test_all: test_small test_medium

test_small: test_pack_small test_unpack_small
test_medium: test_pack_medium test_unpack_medium
test_large: test_pack_large test_unpack_large

test_pack_small: BIN_SIZE=100
test_pack_small: MAX_FILE_SIZE=10

test_pack_medium: BIN_SIZE=100
test_pack_medium: MAX_FILE_SIZE=100

test_pack_large: BIN_SIZE=34091302912
test_pack_large: MAX_FILE_SIZE=34091302912
test_pack_large: SOURCE_PATH=${LARGE_DATA_PATH}
test_unpack_large: SOURCE_PATH=${LARGE_DATA_PATH}

test_pack test_pack_small test_pack_medium test_pack_large:
	@echo
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo; echo "📦📦📦📦 Test: $@ 📦📦📦📦"
	@echo "📦📦📦📦 Testing Packing. Max file size: ${MAX_FILE_SIZE} 📦📦📦📦"
	time python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize $(MAX_FILE_SIZE) --key $(CERTIFICATE)

test_unpack test_unpack_small test_unpack_medium test_unpack_large:
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo "📦📦📦📦 Testing Unpacking. Test: $@ 📦📦📦📦"
	time python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} --key $(PRIVATE_KEY)
	@echo "📦📦📦📦 Verifying test output..."
	@(diff --brief --recursive ${SOURCE_PATH} ${RESTORE_PATH} && echo "Test: $@, Result: [PASSED]") || (echo "Test: $@, Result: [FAILED]" && exit 1)

test_clean:
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@rm -rf ${LARGE_DATA_PATH}/*

init_testdata: init_certificate_pair
	@echo "🛠 creating test dataset for test, in: ${LARGE_DATA_PATH} 🛠"
# TODO increase test data volume.
	@for n in `seq -s " " -f %02g 1 3`; do \
		mkdir -p "${LARGE_DATA_PATH}/$$n"; \
		time dd if=/dev/urandom of="${LARGE_DATA_PATH}/$$n/dummy-1G-$$n" bs=64M count=16 iflag=fullblock; \
	done

init_certificate_pair:
	@echo "🔑 generating RSA certificate pair..."
	mkdir -p ${CERTIFICATE_ROOT}
	openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout ${PRIVATE_KEY} -out ${CERTIFICATE} -subj "/C=ZZ/O=protocol.ai/OU=outercore/CN=packer"


pytest:
	@echo "🔬 running pytest tests"
	python -m pytest test/test_packer.py -o log_cli=true -o log_cli_level=DEBUG --junitxml=test-report.xml.gitignore
