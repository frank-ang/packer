# Packer.

Utility to perform packaging of files for Filecoin deals. Performs: file encryption, large file splitting, and generation of CAR files, in preparation of data storage movement. After data retrieval from Filecoin, performs: CAR file extraction, large file reassembly, file decryption.


![Packer](doc/Packer.drawio.png)



## Notes

Note to self: Passphrases will use "password" for non-production purposes. 

# Encryption / Decryption

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