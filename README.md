# Packer.

[![CircleCI](https://circleci.com/gh/frank-ang/packer/tree/test.svg?style=svg)](https://circleci.com/gh/frank-ang/packer/tree/test)

Utility to perform packaging of files for Filecoin deals. Performs: file encryption, large file splitting, and generation of CAR files, in preparation of data storage movement. After data retrieval from Filecoin, performs: CAR file extraction, large file reassembly, file decryption.


![Packer](doc/Packer.drawio.png)


# Objective.

To provide a tool for packaging large potentially proprietary data sets into the Filecoin network. Objective is to reduce friction for data movement, across both online deal and offline deal paths.

## Benefits:
* Standardization of packaging toolset for large proprietary data sets scenarios.
* Removes lower-level undifferentiated heavy lifting, that the Filecoin ecosystem can reuse in multiple contexts such as "Data storage broker", "Data storage concentrator" e.g. Estuary, Sneakernet provider, Data Client using DIY offline path.

## Functionality

Packing:
* Split large files
* Encrypt files (RSA-AES asymmetric)
* Pack into CAR set
* Parallelism

Unpacking:
* Unpack from CAR set
* Decrypt files
* Join split files into original file
* Restore files into filesystem.

## Source storage system types:

Current supported filesystems:
* POSIX NFS / DASD file system.

Future/Backlog options to support additional sources, particularly cloud object storage:
* Amazon S3, and S3-compatible cloud object storage.
* Azure Blob Storage
* Google Cloud Storage
* Alibaba Cloud Object Storage Service
* Huawei Cloud Object Storage Service

## Encryption / Decryption

Cryptographic methods:
* RSA AES CBC (keypair)

Cryptographic methods TODO:
* RSA AES CBC (symmetric)
* GnuPGP

## Performance.

Initial testing suggests Packer packing rate on 1 instance of AWS EC2 r5d.2xlarge (8 vCPU, 64GB memory, 1x300GiB NVMe), EFS input with 100GB files, output to EBS, RSA-AES encryption, was approximately 120GiB/hr packing rate (2.88TiB/day).

# Quick Start appliance on AWS

If you more interested in automation to generate a CAR set from AWS EFS or AWS S3, a convenience [CloudFormation template](./aws/aws.md) is available to launch an EC2 appliance, configure packer, execute a packing job, and host the packed CAR set on a web server.

# Usage:

```
usage: python packer.py [--pack|--unpack] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-k ENCRYPTION_KEY]

Filecoin filesystem packager/unpackager

options:
  -h, --help            show this help message and exit
  -p, --pack            Pack mode
  -u, --unpack          Unpack mode
  -s SOURCE, --source SOURCE
                        In Pack mode, the path to the original source data. In Unpack mode, the path containing CAR files.
  -t TMP, --tmp TMP     Path to temporary staging directory. Currently, required temp size > 1x of source data size.
  -o OUTPUT, --output OUTPUT
                        Path to write output of packaged or unpackaged content.
  -k KEY, --key KEY     RSA Cryptographic Key or Certificate
  -b BINSIZE, --binsize BINSIZE
                        [optional] Bin size bytes (default: 32000000000)
  -m FILEMAXSIZE, --filemaxsize FILEMAXSIZE
                        [optional] File max size bytes (default: 1073741824)
  -j JOBS, --jobs JOBS  [optional] Job concurrency suggestion (default: 1)

```

# Installation

## Prerequisites

Dependencies.
* Linux OS (tested on Ubuntu 20 and MacOS)
* Python 3.10+, pip
* NodeJS 16.+
* ipfs-car
* rsync
* openssl
* [stream-commp](github.com/filecoin-project/go-fil-commp-hashhash/cmd/stream-commp)

Refer to Cloudformation yaml file for Ubuntu install commands.

## Install.

Clone this repo.
```
make init_testdata
make test
```

# Encryption Keys

Packer currently uses RSA AES encryption. Bring your own keys, or generate a key pair (explained below). 

Users are responsible for observing key management best-practices, please store your keys securely.


## Generate private key and public certificate.

Interactive
```
openssl req -x509 -nodes -days 36500 -newkey rsa:2048 -keyout private_key.pem -out certificate.pem
```

Non-interactive:
```
openssl req -x509 -nodes -days 36500 -newkey rsa:2048 -keyout private_key.pem -out certificate.pem -subj "/C=ZZ/O=protocol.ai/OU=outercore/CN=packer"
```


# Backlog / Caveats

## Backlog Improvements:
TODO:
* AWS Packer AMI with CloudFormation template using IAM instance profile for EFS use-case, on-prem NFS via DX use-case, S3 use-case.
* Manifest file of file-car mappings.
* Toggle encryption.
* S3 support.
* Metrics for job progress.
* Additional cryptographic methods: RSA-AES symmetric; GnuPG
* Compression.
* Filename / dirname obfuscation. (current implementation preserves cleartext path names in the CAR)

See [issues](https://github.com/frank-ang/packer/issues).


## CAVEATS & NOT SUPPORTED:

* Path names are transparently stored in CAR files in clear, although individual files are encrypted. User is responsible for ensuring source filesystem pathnames are hidden (e.g. preprocess all data into TAR files), obfuscated, or otherwise does not contain privacy information.
* POSIX metadata (e.g. mtime) are discarded since CAR files do not preserve file metadata. Workaround is for the user to preprocess all data into TAR files (same workaround as for path name privacy)


# License

This project is licensed under the terms of the [MIT](./LICENSE) license.

