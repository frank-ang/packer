# Packer.

Utility to perform packaging of files for Filecoin deals. Performs: file encryption, large file splitting, and generation of CAR files, in preparation of data storage movement. After data retrieval from Filecoin, performs: CAR file extraction, large file reassembly, file decryption.

## Notes

Note to self: Passphrases will use "password" for non-production purposes. 

## Key generation
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

### Export the public key from GnuPG

```
gpg --export “fingerprint of key” -armor > filecoin_archive_public_key.gpg
```


## Decryption

Data Client performs decryption

```
gpg -d encrypted_test_file > path_to_output_decrypted_file
```

