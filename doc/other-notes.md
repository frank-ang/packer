# Miscellaneous draft notes

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

https://github.com/ipfs/devgrants/blob/master/MICROGRANTS.md
