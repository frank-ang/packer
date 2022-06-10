# CommP stuff.

## ipfs-car does not generate commp.
16:32:04:~/lab/packer % ipfs-car --pack test/source --output test.source.car.gitignore
root CID: bafybeif2bm24pswg6rpeueu4hdibmvnuir2nnz3wnbazzqe5keyh62usnm
  output: test.source.car.gitignore

## Lotus lite client does this:
  16:35:13:~/lab/packer % lotus client commP $HOME/lab/packer/test.source.car.gitignore
CID:  baga6ea4seaqdyxcef4gzd7gpmle7xcmkjbwifzmwvimx7oighq4v33nw7aqmaky
Piece size:  1.984 KiB

## stream-commp does this:
>> Assessment: stream-commp is a suitable utility.

```
go install github.com/filecoin-project/go-fil-commp-hashhash/cmd/stream-commp@latest

cat $HOME/lab/packer/test.source.car.gitignore | ~/go/bin/stream-commp

CommPCid: baga6ea4seaqdyxcef4gzd7gpmle7xcmkjbwifzmwvimx7oighq4v33nw7aqmaky
Payload:                1614 bytes
Unpadded piece:         2032 bytes
Padded piece:           2048 bytes

CARv1 detected in stream:
Blocks:        16
Roots:          1
    1: bafybeif2bm24pswg6rpeueu4hdibmvnuir2nnz3wnbazzqe5keyh62usnm
```

# Manifest File format (DRAFT):

tenets: 
* simplicity, CSV.

per-job fields:
* local timestamp of packing operation.
* dump of PackConfig

per-file fields:
* file-path-origin
* file-path-car: ( original path | .encrypted | .split | .split.encrypted)
   [ wondering.. probably do not need individual processed file CID.. ]
* car: filename
* commP: essential input for offline deals, enables customer to verify PoS.
* [ mtime (optional): POSIX mtime time modified, S3 time modified ]
* [ ext (optional): POSIX permissions attributes, S3 tags, ]

