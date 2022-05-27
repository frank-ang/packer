SHELL=/bin/bash
SOURCE_PATH:=./test/source
LARGE_DATA_PATH:=./test/large-source
XL_DATA_PATH:=./test/xl-source
STAGING_PATH:=./test/staging
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
# Bin Size and Max Filesize (both should be set to identical values) in Bytes
#  For 32GB Sector size, the usable size should be 34,091,302,912 bytes
#  https://lotus.filecoin.io/tutorials/lotus/large-files/
# TODO Verify what should be the optimum value. Test with 34091302912
# UPDATE:
# While the openssl limit tested appears to between 1.8G and 1.9GB for source,
# since the openssl email list points out the 1.48 limit, we should use this as authoritative.
# For safety, lets use 1.0 GB max file size split.
# 
# TODO cleanup comments.
# Considering the encrypted file is slightly larger than source,
#    the 1.8GB encrypted file (1934622378 B) was 1887914 B (1.8 MB) larger than the source file (1932734464 B),
# so, we should apply a padding of at least that size. Increase 1.8 MB to 4 MB just to be cautious.
# 
# FAILED: MAX_FILE_SIZE = (1024 * 1024 * 1024 * 1.48) - ( 1024 * 1024 * 4 ) = 1584943596 (still fails!)
# TRY:    MAX_FILE_SIZE = (1024 * 1024 * 1024 * 1.40) - ( 0 ) = 1503238554
# TODO: Decrypt malloc problem with huge file on openssl... lets try limiting max file.
#    results: MAX_FILE_SIZE: 32GB, 8GB Out of memory.
# To execute the XL-sized test:
# ``
# time make -j 6 init_xldata 
# time make test_xl >> test.log 2>&1
# ```
# MAX_FILE_SIZE >= 2GB size throws malloc memory error on decrypt. Limit is 1.48GB.
BIN_SIZE:=32000000000
MAX_FILE_SIZE=1073741824
CERTIFICATE_ROOT:=./test/security.rsa.gitignore
CERTIFICATE:=${CERTIFICATE_ROOT}/certificate.pem
PRIVATE_KEY:=${CERTIFICATE_ROOT}/private_key.pem
AWS_CFN_TEMPLATE_FILE:=./test/cloudformation-load-test.yml

-include config.mk.gitignore

help:
	echo "Packer makefile"
	echo "MAX_FILE_SIZE $(MAX_FILE_SIZE)"

test: clean test_all

test_all: test_small test_medium

test_small: test_pack_small test_unpack_small
test_medium: test_pack_medium test_unpack_medium
test_large: test_pack_large test_unpack_large
test_xl: test_pack_xl test_unpack_xl

test_pack_small: BIN_SIZE=4096
test_pack_small: MAX_FILE_SIZE=40

test_pack_medium: BIN_SIZE=10000
test_pack_medium: MAX_FILE_SIZE=100

test_pack_large: SOURCE_PATH=${LARGE_DATA_PATH}
test_pack_xl: SOURCE_PATH=${XL_DATA_PATH}

test_pack_small test_pack_medium test_pack_large test_pack_xl:
	@echo
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo; echo "📦📦📦📦 Test: $@ 📦📦📦📦"
	@echo "📦📦📦📦 Testing Packing. Max file size: ${MAX_FILE_SIZE} 📦📦📦📦"
	time python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize $(MAX_FILE_SIZE) --key $(CERTIFICATE)

test_unpack_large: SOURCE_PATH=${LARGE_DATA_PATH}
test_unpack_xl: SOURCE_PATH=${XL_DATA_PATH}

test_unpack_small test_unpack_medium test_unpack_large test_unpack_xl:
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo "📦📦📦📦 Testing Unpacking. Test: $@ 📦📦📦📦"
	time python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} --key $(PRIVATE_KEY)
	@echo "📦📦📦📦 Verifying test output..."
	@(diff --brief --recursive ${SOURCE_PATH} ${RESTORE_PATH} && echo "Test: $@, Result: [PASSED]") || (echo "Test: $@, Result: [FAILED]" && exit 1)

clean: clean_test

clean_test:
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}
	@rm -rf ${CAR_PATH}
	@rm -rf ${RESTORE_PATH}
	@rm -rf ${LARGE_DATA_PATH}

clean_xldata:
	@rm -rf ${XL_DATA_PATH}

init_testdata: clean_test init_certificate_pair

init_certificate_pair:
	@echo "🔑 generating RSA certificate pair..."
	mkdir -p ${CERTIFICATE_ROOT}
	openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout ${PRIVATE_KEY} -out ${CERTIFICATE} -subj "/C=ZZ/O=protocol.ai/OU=outercore/CN=packer"


init_largedata: init_testdata
	@echo "🛠 creating test dataset for test, in: ${LARGE_DATA_PATH} 🛠"
	@echo "##🛠 creating 1KiB files..."
	./test/gen-large-test-data.sh -c 1000 -s 1024 -p KiB -d "${LARGE_DATA_PATH}"
	@echo "##🛠 creating 1MiB files..."
	./test/gen-large-test-data.sh -c 10 -s 1048576 -p MiB -d ${LARGE_DATA_PATH}
	@echo "##🛠 creating 1GiB files..."
	./test/gen-large-test-data.sh -c 2 -s 1073741824 -p GiB -d ${LARGE_DATA_PATH}
	@echo "completed test data creation."
	ls -lh "${LARGE_DATA_PATH}/1"
	du -sh "${LARGE_DATA_PATH}"


# Init Jumbo sized test data in parallel.
# Usage:
# ```
# make init_testdata  # prereq should be run in serial.
# make -j 5 init_xldata  # parallel execution.
# ```
# Generate random test data on-demand, e.g.
#  *   1TB test: 9x100GB 90x1GB 9000x1MB  1000000x1KB 
#  * 200GB test: 1000*1K + 99*1M + 2*1G + 1*50G =  52 G
# Execution times:
#  * Serial   200GB on Macbook pro: ~10m
#  * Serial   200GB on AWS (EC2 r5.2xlarge, 1TB gp3 EBS): 29m27.544s; 30m28.261s
#  * Parallel 200GB on AWS (EC2 r5.2xlarge, 1TB gp3 EBS): 27m20.517s; 26m52.510s (looks like bottleneck is in jumbo generation?)
#  *   1TB on AWS (EC2 2xlarge, 3000GB gp3 EBS): TODO

# Side Note: Not cost-optimal to store & retrieve pre-generated test data from S3.
# E.g. 200GB on AWS S3, egress once per month to Internet. 
# Finding: AWS Egress cost will be multiples of S3 standard storage cost.
# *  https://calculator.aws/#/estimate?id=121d54cc893c4fc91220b34547dd37af9d80cbdd
#
init_xldata: init_testdata init_xldata_1KiB init_xldata_1MiB init_xldata_1GiB init_xldata_jumbo
	@echo "🛠 completed jumbo test data creation in: ${XL_DATA_PATH} 🛠"

# 1000 1KiB files
init_xldata_1KiB:
	@echo "##🛠 creating 1KiB files..."
	./test/gen-large-test-data.sh -c 1000 -s 1024 -p dummy-KiB -d "${XL_DATA_PATH}/1KiB"

# 1000 1MiB files
init_xldata_1MiB:
	@echo "##🛠 creating 1MiB files..." 
	./test/gen-large-test-data.sh -c 999 -s $$(( 1024 * 1024)) -p dummy-MiB -d "${XL_DATA_PATH}/1MiB"

# 99 1GiB files
init_xldata_1GiB:
	@echo "##🛠 creating 1GiB files..."
	./test/gen-large-test-data.sh -c 99 -s $$(( 1024 * 1024 * 1024)) -p dummy-GiB -d "${XL_DATA_PATH}/1GiB"

# 1 100GiB file
init_xldata_jumbo: 
	@echo "##🛠 creating 100GiB files..."
	./test/gen-large-test-data.sh -c 1 -s $$(( 1024 * 1024 * 1024 * 100 )) -p dummy-100GiB -d "${XL_DATA_PATH}/100GiB"


pytest:
	@echo "🔬 running pytest tests"
	python -m pytest test/test_packer.py -o log_cli=true -o log_cli_level=DEBUG --junitxml=test-report.xml.gitignore


create_load_test_instance:
	@echo "Launching AWS EC2 instance for load test".
	aws cloudformation validate-template --template-body file://${AWS_CFN_TEMPLATE_FILE}
	aws cloudformation deploy --capabilities CAPABILITY_IAM \
      --template-file ./${AWS_CFN_TEMPLATE_FILE}  \
      --parameter-overrides "VPC=${AWS_VPC}" "AZ=${AWS_AZ}" "SubnetId=${AWS_SUBNET}" \
         "KeyPair=${AWS_KEY_PAIR}" "SecurityGroup=${AWS_SECURITY_GROUP}" "InstanceProfile=${AWS_INSTANCE_PROFILE}" \
      --stack-name "filecoin-packer-test" \
      --tags "project=filecoin"


delete_load_test_instance:
	aws cloudformation delete-stack --stack-name filecoin-packer-test


wait_stack_deleted:
	aws cloudformation wait stack-delete-complete --stack-name filecoin-packer-test


recreate_load_test_instance: delete_load_test_instance wait_stack_deleted create_load_test_instance
