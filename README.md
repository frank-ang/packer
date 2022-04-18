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

Extensibility possibilities to support multiple source storage systems:
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

# Sample GPG Encryption / Decryption

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

# TODO

Apply for dev microgrant? 
https://github.com/ipfs/devgrants/blob/master/MICROGRANTS.md

# TODO
Angelo. Box interface.