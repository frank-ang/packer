# Debug decrypt problem:
"RE: Malloc failure when decrypting files larger 1.48 GB with openssl smime"
https://www.mail-archive.com/openssl-users@openssl.org/msg72468.html

# ENCRYPT
##  Original problem: decrypt fails on 2.1GB file. 
```
openssl smime -encrypt -binary -aes-256-cbc -stream -in test/staging/CAR0/100GiB/1/dummy-100GiB-1.split.1 \
  -out test/staging/CAR0/100GiB/1/dummy-100GiB-1.split.1.encrypted \
  -outform DER ./test/security.rsa.gitignore/certificate.pem

openssl smime -decrypt -binary -in test/staging/TEMP_STAGING/100GiB/1/dummy-100GiB-1.split.1.encrypted -inform DER -out /root/packer/test/staging/TEMP_STAGING/100GiB/1/dummy-100GiB-1.split.1 -inkey ./test/security.rsa.gitignore/private_key.pem
```

##  Retry: gen 1.48GB data file, encrypt.  1.48GB = 1024 * 1024 * 1024 * 1.48 = 1589137900
```
# 1.48G. Successful! 
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.48 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 1589137408, 

# 1.49G. Successful!
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.49 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 1599875072

# 1.6G. Successful !?
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.6 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 1717986304

# 2.0G. FAILED. as expected.
# Error reading S/MIME message
# 140462005003584:error:07069041:memory buffer routines:BUF_MEM_grow_clean:malloc failure:../crypto/buffer/buffer.c:128:
# 140462005003584:error:0D06B041:asn1 encoding routines:asn1_d2i_read_bio:malloc failure:../crypto/asn1/a_d2i_fp.c:190:

dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 2 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" 

# 1.8G: Successful !?
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.8 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 1932734464

# 1.9G. Malloc Failure.
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.9 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 

# 1.8G: Repeatability Test. SUCCEEDED...
dd if=/dev/urandom of="test/staging/candidate.source" bs=1024 count=`printf %.0f $(echo "1024 * 1024 * 1024 * 1.8 / 1024" | bc)` iflag=fullblock
ls -l "test/staging/candidate.source" # actual file size: 1932734464


####  The following to be run on suitable candidate source file.
## Encrypt
openssl smime -encrypt -binary -aes-256-cbc -stream -in test/staging/candidate.source \
  -out test/staging/candidate.encrypted \
  -outform DER ./test/security.rsa.gitignore/certificate.pem
ls -lh "test/staging/candidate.encrypted"
## Try candidate encrypted file.
openssl smime -decrypt -binary -in test/staging/candidate.encrypted \
    -inform DER -out test/staging.decrypted \
    -inkey ./test/security.rsa.gitignore/private_key.pem
diff test/staging/candidate.source test/staging/candidate.decrypted

```

# Assessment:
While the openssl limit tested appears to between 1.8G and 1.9GB for source,
since the openssl email list points out the 1.48 limit, we should use this as authoritative.

Considering the encrypted file is slightly larger than source, 
    the 1.8GB encrypted file (1934622378 B) was 1887914 B (1.8 MB) larger than the source file (1932734464 B),
so, we should apply a padding of at least that size. Increase 1.8 MB to 4 MB just to be cautious.
So MAX_FILE_SIZE should be: (1024 * 1024 * 1024 * 1.48) - ( 1024 * 1024 * 4 )

