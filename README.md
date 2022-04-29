# Packer.

Utility to perform packaging of files for Filecoin deals. Performs: file encryption, large file splitting, and generation of CAR files, in preparation of data storage movement. After data retrieval from Filecoin, performs: CAR file extraction, large file reassembly, file decryption.


![Packer](doc/Packer.drawio.png)


# Objective.

To provide a toolset for packaging large potentially proprietary data sets. Objective is to reduce friction for data movement, across both online deal and offline deal paths.

## Benefits:
* Standardization of packaging toolset for large proprietary data sets scenarios.
* Removes lower-level undifferentiated heavy lifting, that the Filecoin ecosystem can reuse in multiple contexts such as "Data storage broker", "Data storage concentrator" e.g. Estuary, Sneakernet provider, Data Client using DIY offline path.

## Supported source storage system types (for MVP):
* NFS / DASD / Posix file system.

Extensibility possibilities to support additional source storage systems, particularly cloud object storage:
* Amazon S3, and S3-compatible cloud object storage.
* Azure Blob Storage
* Google Cloud Storage
* Alibaba Cloud Object Storage Service
* Huawei Cloud Object Storage Service

## Encryption / Decryption

Cryptographic methods:
* RSA 4096 (for MVP)
* GnuPGP

## Testing & Benchmarking

Post-MVP, it will be essential to run scalability tests and benchmarks.  

# Usage concept:

```bash
NAME
    packer - Filecoin filesystem packager/unpackager

SYNOPSIS

    python packer.py [-p|-u] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-e TODO]

OPTIONS

    -p, --pack
        pack mode

    -u, --unpack
        unpack mode

    -s SOURCE_PATH, --source SOURCE_PATH
        During packing, the path to the pre-packed source data.
        During unpacking, the path containing CAR files of packed data.

    -t TEMP_PATH, --temp TEMP_PATH
        Path to temporary working directory. 

    -o OUTPUT_PATH, --output OUTPUT_PATH
        Path to write final output of packaged or unpackaged content.
        
    -b BIN_SIZE, --bin BIN_SIZE
        BIN_SIZE in bytes, default 32GB

    -e, --encryption TODO
        TODO encryption key stuff.

    -h, --help
        help
```


# Prerequisites

Install ipfs-car Node package globally.
```bash
npm install -g ipfs-car
```

# TODO notes.
## Sample GPG Encryption / Decryption

## Prep keys
Generate sender's GPG public and secret key.

```
gpg --full-generate-key
gpg --list-secret-keys
gpg --list-keys
```

Generate recipient's GPG public and secret key key, for testing.
```
RECIPIENT_HOMEDIR=$HOME/.gnupg.recipient.test
gpg --homedir=$RECIPIENT_HOMEDIR --full-generate-key
gpg --homedir=$RECIPIENT_HOMEDIR --list-secret-keys
gpg --homedir=$RECIPIENT_HOMEDIR --list-keys
```

At this stage, assume dev/testing Passphrases can use "password". 

## Encryption

```
gpg --encrypt --output data.encrypted --recipient frank@fil.org data.txt
```

If public key export is required.
```
gpg --export “fingerprint of key” -armor > filecoin_archive_public_key.gpg
```

## Decryption

Data Client performs decryption

```
gpg -d data.encrypted > data.decrypted
```

## Dev microgrant?

Apply for dev microgrant? 
https://github.com/ipfs/devgrants/blob/master/MICROGRANTS.md

## Check for existing code that could be re-used?

Check with Angelo about any prior similar work. Stefaan: "Box interface"?.

## Roadmap / backlog.

* AWS Packer AMI with CloudFormation template using IAM instance profile for EFS use-case, on-prem NFS via DX use-case, S3 use-case.
* S3 support.
* Compression.

