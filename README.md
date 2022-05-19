# Packer.

[![CircleCI](https://circleci.com/gh/frank-ang/packer/tree/test.svg?style=svg)](https://circleci.com/gh/frank-ang/packer/tree/test)

Utility to perform packaging of files for Filecoin deals. Performs: file encryption, large file splitting, and generation of CAR files, in preparation of data storage movement. After data retrieval from Filecoin, performs: CAR file extraction, large file reassembly, file decryption.


![Packer](doc/Packer.drawio.png)


# Objective.

To provide a tool for packaging large potentially proprietary data sets into the Filecoin network. Objective is to reduce friction for data movement, across both online deal and offline deal paths.

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
* RSA AES CBC
* GnuPGP (TODO)

## Testing & Benchmarking

Post-MVP, it will be essential to run scalability tests and benchmarks.  

# Usage:

```bash
NAME
    packer - Filecoin filesystem packager/unpackager

SYNOPSIS

    python packer.py [-p|-u] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-k ENCRYPTION_KEY]

OPTIONS

    -p, --pack
        pack mode

    -u, --unpack
        unpack mode

    -s SOURCE_PATH, --source SOURCE_PATH
        During packing, the path to the pre-packed source data.
        During unpacking, the path containing CAR files of packed data.

    -t TEMP_PATH, --temp TEMP_PATH
        Path to temporary staging directory. 

    -o OUTPUT_PATH, --output OUTPUT_PATH
        Path to write final output of packaged or unpackaged content.
        
    -b BIN_SIZE, --bin BIN_SIZE
        BIN_SIZE in bytes, default 32GB

    -k, --key
        Encryption certificate or private key.

    -h, --help
        help
```


# Installation

## Prerequisites

Ensure dependencies are installed.
* Linux OS (tested on Ubuntu and MacOS)
* Python 3.10+
* Rsync
* NodeJS ipfs-car

```bash
sudo apt-get update -y
sudo apt-get install -y rsync
sudo npm install -g ipfs-car
pip install -r requirements.txt
```

## Install.

Clone this repo.

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

# Backlog.

Improvements:
* AWS Packer AMI with CloudFormation template using IAM instance profile for EFS use-case, on-prem NFS via DX use-case, S3 use-case.
* S3 support.
* Compression.
* Filename / dirname obfuscation. (current implementation is in clear)
* Output manifest of file-car mappings.

See [issues](https://github.com/frank-ang/packer/issues).


# License

This project is licensed under the terms of the [MIT](./LICENSE) license.

---

# Misc notes. (TODO cleanup notes)
## Sample GPG Encryption / Decryption

### Prep keys
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

### Encryption

```
gpg --encrypt --output data.encrypted --recipient frank@fil.org data.txt
```

If public key export is required.
```
gpg --export “fingerprint of key” -armor > filecoin_archive_public_key.gpg
```

### Decryption

Data Client performs decryption

```
gpg -d data.encrypted > data.decrypted
```


## Sample RSA 4096 asymmetric + DES/AES symmetric encryption / decryption.

Generate a set of key pairs:

```
# encrypted key with passphrase
openssl genrsa -aes256 -out alice_private.aes256.pem 1024

# Or, unencrypted key without passphrase
openssl genrsa -out alice_private.pem 1024

# Extract the public keys
openssl rsa -in alice_private.pem -pubout > alice_public.pem
```

Encrypt & Decrypt a message
```
openssl rsautl -encrypt -inkey alice_public.pem -pubin -in top_secret.txt -out top_secret.enc

openssl rsautl -decrypt -inkey alice_private.pem -in top_secret.enc > top_secret.decrypted

```

Symmetric key generation, encryption, decryption.
```
openssl rand 128 > symmetric_keyfile.key
openssl enc -in top_secret.txt -out top_secret.txt.enc -e -aes256 -k symmetric_keyfile.key
openssl enc -in top_secret.txt.enc -out top_secret.txt.decrypted -d -aes256 -k symmetric_keyfile.key
```

### Generate private key and public certificate.
```
openssl req -x509 -nodes -days 100000 -newkey rsa:2048 -keyout private_key.pem -out certificate.pem

# non-interactive:
openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout private_key.pem -out certificate.pem -subj "/C=ZZ/O=protocol.ai/OU=outercore/CN=packer"
```

### Encryption/decryption combining both symmetric+asymmetric. Should work for large binary files:

Ref: https://gist.github.com/dreikanter/c7e85598664901afae03fedff308736b

```
openssl smime -encrypt -binary -aes-256-cbc -in top_secret.txt -out top_secret.txt.enc -outform DER certificate.pem
openssl smime -decrypt -binary -in top_secret.txt.enc -inform DER -out top_secret.txt.decrypted -inkey private_key.pem
```

### Test openssl with larger file.

```
# create 10MB file (1024KB * 10).
dd if=/dev/zero of=junk.dat bs=1024 count=0 seek=$[1024*10]
openssl smime -encrypt -binary -aes-256-cbc -in junk.dat -out junk.dat.enc -outform DER certificate.pem
openssl smime -decrypt -binary -in junk.dat.enc -inform DER -out junk.dat.decrypted -inkey private_key.pem
diff junk.dat.decrypted junk.dat 
```

Compare vs using PEM output format, and S/MIME output format.
```
openssl smime -encrypt -binary -aes-256-cbc -in junk.dat -out junk.dat.aes-pem-enc -outform PEM certificate.pem
openssl smime -decrypt -binary -in junk.dat.aes-pem-enc -inform PEM -out junk.dat.aes-pem-decrypted -inkey private_key.pem

openssl smime -encrypt -binary -aes-256-cbc -in junk.dat -out junk.dat.aes-smime-enc certificate.pem
openssl smime -decrypt -binary -in junk.dat.aes-smime-enc -out junk.dat.aes-smime-decrypted -inkey private_key.pem

```

> Observations:
> 
> DER formatted encrypted file is larger (1376 Bytes) than unencrypted file. Binary.
> RSA formatted encrypted file is larger (35+%) than unencrypted file. PKCS#7 ASCII format.
> S/MIME formatted encrypted file is larger (35+%) than unencrypted file. S/MIME ASCII format.

## Dev microgrant?

Apply for dev microgrant? 
https://github.com/ipfs/devgrants/blob/master/MICROGRANTS.md

## Check for existing code that could be re-used?

Check with Angelo about any prior similar work. Stefaan: "Box interface"?.

## BUGS.

TODO investigate

> init_largedata Error 1 

```
# time make init_largedata
...
1073741824 bytes (1.1 GB, 1.0 GiB) copied, 14.4031 s, 74.5 MB/s
34179687+0 records in
34179687+0 records out
34999999488 bytes (35 GB, 33 GiB) copied, 333.105 s, 105 MB/s
make: *** [Makefile:94: init_largedata] Error 1

real	5m33.166s
user	0m26.941s
sys	4m25.409s
```