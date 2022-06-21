SHELL=/bin/bash
SOURCE_PATH:=./test/source
LARGE_DATA_PATH:=./test/large-source
XL_DATA_PATH:=/nfs/xl-source
STAGING_PATH:=./test/staging
CAR_PATH:=./test/car
RESTORE_PATH:=./test/restore
# Note: 32GB Sector usable size should be 34,091,302,912 bytes
#  https://lotus.filecoin.io/tutorials/lotus/large-files/
#
# Decision to use 1 GB max file size is due to an openssl decryption scaling limitation.
#   Openssl email list points out the 1.48 limit, we should use this as authoritative.
#   Openssl source file size limit during decryption has been tested on Ubuntu EC2 to be 1.8G to 1.9GB.
#   To be conservative, this implementation will use 1.0 GB max file size split to keep well within the limit.
# 
# Observation: Encryption size overhead.
# 	Encrypted file has been tested to be slightly larger than source,
#    a 1.8GB encrypted file (1934622378 B) was larger than the source file (1932734464 B) by 1887914 B (1.8 MB)
# 
# To run an XL-sized test, start a tmux session, and run the following:
# ```
# make init_testdata
# time make -j 6 init_xldata 
# time make test_xl >> test.log 2>&1
# ```
# INSTRUCTIONS: Create the following config file, based on template file: config.mk
-include config.mk.gitignore

BIN_SIZE:=32000000000
MAX_FILE_SIZE=1073741824
CERTIFICATE_ROOT:=./test/security.rsa.gitignore
CERTIFICATE:=${CERTIFICATE_ROOT}/certificate.pem
PRIVATE_KEY:=${CERTIFICATE_ROOT}/private_key.pem
AWS_LOAD_TEST_TEMPLATE:=./aws/cloudformation-load-test.yml
AWS_APPLIANCE_TEMPLATE:=./aws/filecoin-packer-aws-appliance.yml
AWS_TEST_DATASOURCES_TEMPLATE:=./aws/cloudformation-test-datasources.yml
JOBS:=1


help:
	echo "Packer makefile"
	echo "MAX_FILE_SIZE $(MAX_FILE_SIZE)"

test: clean test_all

test_all: test_small test_medium

test_small: test_pack_small test_unpack_small
test_medium: test_pack_medium test_unpack_medium
test_large: test_pack_large test_unpack_large
test_xl: init_testdata test_pack_xl test_unpack_xl

test_pack_small: BIN_SIZE=4096
test_pack_small: MAX_FILE_SIZE=40
test_pack_medium: BIN_SIZE=10000
test_pack_medium: MAX_FILE_SIZE=100
test_pack_large: SOURCE_PATH=${LARGE_DATA_PATH}
test_pack_large: JOBS=1
test_pack_xl: SOURCE_PATH=${XL_DATA_PATH}
test_pack_xl: JOBS=8
test_pack_xl: STAGING_PATH=/local/staging
test_pack_xl: CERTIFICATE_ROOT=/root/security.rsa.gitignore
test_pack_xl: init_testdata
test_pack_small test_pack_medium test_pack_large test_pack_xl:
	@echo
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo; echo "📦📦📦📦 Test: $@ 📦📦📦📦"
	@echo "📦📦📦📦 Testing Packing. Max file size: ${MAX_FILE_SIZE} 📦📦📦📦"
	time python ./packer.py --pack --source ${SOURCE_PATH} --tmp ${STAGING_PATH} --output ${CAR_PATH} --binsize ${BIN_SIZE} --filemaxsize $(MAX_FILE_SIZE) --key $(CERTIFICATE) --jobs $(JOBS)

test_unpack_large: SOURCE_PATH=${LARGE_DATA_PATH}
test_unpack_large: JOBS=1
test_unpack_xl: STAGING_PATH=/local/staging
test_unpack_xl: SOURCE_PATH=${XL_DATA_PATH}
test_unpack_xl: JOBS=8
test_unpack_small test_unpack_medium test_unpack_large test_unpack_xl:
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@echo "📦📦📦📦 Testing Unpacking. Test: $@ 📦📦📦📦"
	time python ./packer.py --unpack --source ${CAR_PATH} --tmp ${STAGING_PATH} --output ${RESTORE_PATH} --key $(PRIVATE_KEY) --jobs $(JOBS)
	@echo "📦📦📦📦 Verifying test output..."
	@(time diff --brief --recursive ${SOURCE_PATH} ${RESTORE_PATH} && echo "Test: $@, Result: [PASSED]") || (echo "Test: $@, Result: [FAILED]" && exit 1)


pytest: clean init_testdata
	@echo "🔬 running pytest tests"
	python -m pytest test/test_packer.py -o log_cli=true -o log_cli_level=DEBUG --junitxml=test-report.xml.gitignore


clean: clean_test

clean_test:
	@echo "🧹 cleaning... 🧹"
	@rm -rf ${STAGING_PATH}/*
	@rm -rf ${CAR_PATH}/*
	@rm -rf ${RESTORE_PATH}/*
	@rm -rf ${LARGE_DATA_PATH}/*

clean_xldata:
	@rm -rf ${XL_DATA_PATH}/*

init_aws_secrets: init_testdata
	aws secretsmanager create-secret --name FilecoinPackerPrivateKey \
              --description "RSA private key PEM for Filecoin encryption" \
              --secret-string file://${PRIVATE_KEY}
	aws secretsmanager create-secret --name FilecoinPackerCertificate \
              --description "RSA private key PEM for Filecoin encryption" \
              --secret-string file://${CERTIFICATE}
	aws secretsmanager get-secret-value --secret-id FilecoinPackerPrivateKey


init_testdata: clean_test init_certificate_pair

init_certificate_pair:
	@echo "🔑 generating RSA certificate pair..."
	mkdir -p ${CERTIFICATE_ROOT}
	openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout ${PRIVATE_KEY} -out ${CERTIFICATE} -subj "/C=ZZ/O=protocol.ai/OU=outercore/CN=packer"


init_largedata: init_testdata
	@echo "🛠 creating test dataset for large test, in: ${LARGE_DATA_PATH}, bin count: ${JOBS}🛠"

	@echo "##🛠 creating 1KiB files..."
	@for (( bin=1; bin<=10; bin++ )); do ./test/gen-large-test-data.sh -c 10 -s 1024 -p dummy-KiB -d "${LARGE_DATA_PATH}/$$bin"; done

	@echo "##🛠 creating 1MiB files..."
	@for (( bin=1; bin<=10; bin++ )); do ./test/gen-large-test-data.sh -c 10 -s $$(( 1024 * 1024 )) -p dummy-MiB -d "${LARGE_DATA_PATH}/$$bin"; done

	@echo "##🛠 creating 1GiB files..."
	@for (( bin=1; bin<=2; bin++ )); do ./test/gen-large-test-data.sh -c 1 -s $$(( 1024 * 1024 * 1024 )) -p dummy-GiB -d "${LARGE_DATA_PATH}/$$bin"; done

	echo "##🛠 creating 3GiB files...";
	@for (( bin=3; bin<=4; bin++ )); do ./test/gen-large-test-data.sh -c 1 -s $$(( 1024 * 1024 * 1024 * 3 )) -p dummy-3GiB -d "${LARGE_DATA_PATH}/$$bin"; done
	@echo "🛠 completed large test data creation. File count: "`find ${LARGE_DATA_PATH}/ -type f | wc -l`" , total size: "`du -sh ${LARGE_DATA_PATH}`" 🛠"

# Init Jumbo sized test data in parallel.
# Generate random test data on-demand, e.g.
#  *   1TB test: 9x100GB 90x1GB 9000x1MB  1000000x1KB 
#  * 200GB test: 1000*1K + 99*1M + 2*1G + 1*50G =  52 G
# Execution times:
#  * Serial   200GB on Macbook pro: ~10m
#  * Serial   200GB on AWS (EC2 r5.2xlarge, 1TB gp3 EBS): 29m27.544s; 30m28.261s
#  * Parallel 200GB on AWS (EC2 r5.2xlarge, 1TB gp3 EBS): 27m20.517s; 26m52.510s (looks like bottleneck is in jumbo generation?)
#  * Parallel 100GB on AWS with EC2 r5d.2xlarge, 1TB gp3 EBS, NVMe SSD at /local
#  *   1TB on AWS (EC2 2xlarge, 3000GB gp3 EBS): TODO
#
# Side Note: Not cost-optimal to store & retrieve pre-generated test data from S3.
# E.g. 200GB on AWS S3, egress once per month to Internet. 
# Finding: AWS Egress cost will be multiples of S3 standard storage cost.
# *  https://calculator.aws/#/estimate?id=121d54cc893c4fc91220b34547dd37af9d80cbdd
#
# Generate bins of test data with 10 parallel processes:
# ```time make -j 10 init_xldata```
init_xldata: 0.init_xldata_bin 1.init_xldata_bin 2.init_xldata_bin 3.init_xldata_bin 4.init_xldata_bin 5.init_xldata_bin 6.init_xldata_bin 7.init_xldata_bin 8.init_xldata_bin 9.init_xldata_bin
	@echo "🛠 completed jumbo test data creation. File count: "`find "${XL_DATA_PATH}/ -type f" | wc -l`" , total size: "`du -sh ${XL_DATA_PATH}`" 🛠"


# Generate test data in 1 bin. 10GB
%.init_xldata_bin:
	@mkdir -p ${XL_DATA_PATH}
	@echo "##🛠 Bin:$*, creating 1KiB files..."
	./test/gen-large-test-data.sh -c 1000 -s 1024 -p dummy-KiB -d "${XL_DATA_PATH}/$*/1KiB"
	@echo "##🛠 Bin:$*, creating 1MiB files..." 
	./test/gen-large-test-data.sh -c 10 -s $$(( 1024 * 1024)) -p dummy-MiB -d "${XL_DATA_PATH}/$*/1MiB"
	@echo "##🛠 Bin:$*, creating 1GiB files..."
	./test/gen-large-test-data.sh -c 1 -s $$(( 1024 * 1024 * 1024)) -p dummy-GiB -d "${XL_DATA_PATH}/$*/1GiB"
	@echo "##🛠 Bin:$*, creating 9GiB files..."
	./test/gen-large-test-data.sh -c 1 -s $$(( 1024 * 1024 * 1024 * 9 )) -p dummy-9GiB -d "${XL_DATA_PATH}/$*/9GiB"


# AWS resources.
create_load_test_instance:
	@echo "Launching AWS EC2 instance for load test".
	aws cloudformation validate-template --template-body file://${AWS_LOAD_TEST_TEMPLATE}
	time aws cloudformation deploy --capabilities CAPABILITY_IAM \
      --template-file ${AWS_LOAD_TEST_TEMPLATE}  \
      --parameter-overrides "VPC=${AWS_VPC}" "AZ=${AWS_AZ}" "SubnetId=${AWS_SUBNET}" \
         "KeyPair=${AWS_KEY_PAIR}" "SecurityGroup=${AWS_SECURITY_GROUP}" "InstanceProfile=${AWS_INSTANCE_PROFILE}" \
      --stack-name "filecoin-packer-load-test" \
      --tags "project=filecoin"
	@echo "Packer Load Test EC2 Ubuntu instance IP: "`aws cloudformation describe-stacks --stack-name filecoin-packer-load-test | jq '.Stacks[].Outputs[]|select(.OutputKey=="PublicIP").OutputValue' -r`

delete_load_test_instance:
	aws cloudformation delete-stack --stack-name filecoin-packer-load-test

wait_delete_load_test_stack:
	aws cloudformation wait stack-delete-complete --stack-name filecoin-packer-load-test

recreate_load_test_instance: delete_load_test_instance wait_delete_load_test_stack create_load_test_instance

create_appliance:
	@echo "Creating packer appliance AWS stack..."
	aws cloudformation validate-template --template-body file://${AWS_APPLIANCE_TEMPLATE}
	time aws cloudformation deploy --capabilities CAPABILITY_IAM \
      --template-file ${AWS_APPLIANCE_TEMPLATE}  \
      --parameter-overrides "VPC=${AWS_VPC}" "AZ=${AWS_AZ}" "SubnetId=${AWS_SUBNET}" \
         "KeyPair=${AWS_KEY_PAIR}" "SecurityGroup=${AWS_SECURITY_GROUP}" "InstanceProfile=${AWS_INSTANCE_PROFILE}" \
      --stack-name "filecoin-packer-appliance-test" \
      --tags "project=filecoin"
	@echo "Packer Load Test EC2 Ubuntu instance IP: "`aws cloudformation describe-stacks --stack-name filecoin-packer-appliance-test | jq '.Stacks[].Outputs[]|select(.OutputKey=="PublicIP").OutputValue' -r`

delete_appliance:
	@echo "Deleting packer appliance AWS stack..."
	aws cloudformation delete-stack --stack-name filecoin-packer-appliance-test

recreate_appliance: delete_appliance wait_delete_appliance create_appliance
	@echo "Recreated packer appliance AWS stack..."

wait_delete_appliance:
	aws cloudformation wait stack-delete-complete --stack-name filecoin-packer-appliance-test

create_test_datasources:
	@echo "Creating Test Datasources in AWS".
	aws cloudformation validate-template --template-body file://${AWS_TEST_DATASOURCES_TEMPLATE}
	time aws cloudformation deploy --capabilities CAPABILITY_IAM \
      --template-file ${AWS_TEST_DATASOURCES_TEMPLATE}  \
      --parameter-overrides "VPC=${AWS_VPC}" "AZ=${AWS_AZ}" "SubnetId=${AWS_SUBNET}" \
         "SecurityGroup=${AWS_SECURITY_GROUP}" \
      --stack-name "filecoin-packer-test-datasources" \
      --tags "project=filecoin"
	@echo "Packer Load Test EC2 Ubuntu instance IP: "`aws cloudformation describe-stacks --stack-name filecoin-packer-test-datasources | jq '.Stacks[].Outputs[]|select(.OutputKey=="FileSystemDnsName").OutputValue' -r`

delete_test_datasources:
	@echo "Deleting Test Datasources..."
	aws cloudformation delete-stack --stack-name filecoin-packer-test-datasources


run_packer_job:
	@echo "📦📦📦📦 Running Packer Job script ... 📦📦📦📦"
	./packer_job.sh
	@echo "📦📦📦📦 Completed Packer Job script ... 📦📦📦📦"


publish_cloudformation_template:
	@echo "updating cloudformation template to AWS S3"
	aws s3 cp ${AWS_APPLIANCE_TEMPLATE} s3://filecoin-packer/filecoin-packer-aws-appliance.yml
#https://filecoin-packer.s3.ap-southeast-1.amazonaws.com/filecoin-packer-aws-appliance.yml