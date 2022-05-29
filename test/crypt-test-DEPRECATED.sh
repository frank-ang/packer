#!/bin/bash

## Symmetric
# time gpg --symmetric --batch --passphrase 123 --output blob.gpg -z 0 blob
# time gpg --decrypt --batch --passphrase 123 --output blob blob.gpg
## Asymmetric
# time gpg --encrypt --recipient fred --output blob.gpg blob
# time gpg --decrypt --batch --output blob blob.gpg



#gpg --encrypt --recipient frank --output data.encrypted
#gpg --decrypt --output data.decrypted data.encrypted
#gpg --output myfile.txt.gpg --encrypt --recipient your.friend@yourfriendsdomain.com  myfile.txt
