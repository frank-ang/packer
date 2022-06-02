import pytest
from filecoin_packer.pack import PackConfig 
from packer import pack, unpack
import logging

SOURCE_PATH="./test/source"
LARGE_DATA_PATH="./test/large-source"
STAGING_PATH="./test/staging"
CAR_PATH="./test/car"
RESTORE_PATH="./test/restore"
# Bin Size and Max Filesize (both should be set to identical values) in Bytes
#  For 32GB Sector size, the usable size should be 34,091,302,912 bytes
#  https://lotus.filecoin.io/tutorials/lotus/large-files/
# TODO Verify what should be the optimum value. Test with 34091302912
#BIN_SIZE=32000000000
#MAX_FILE_SIZE=32000000000
BIN_SIZE=100
MAX_FILE_SIZE=100
CERTIFICATE_ROOT="./test/security.rsa.gitignore"
CERTIFICATE=CERTIFICATE_ROOT + "/certificate.pem"
PRIVATE_KEY=CERTIFICATE_ROOT + "/private_key.pem"

logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.DEBUG)


def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 4

@pytest.mark.order(1)
def test_pack_medium():
    logging.debug("##### #####  test_pack_medium ()   ##### #####")
    config = PackConfig(SOURCE_PATH, CAR_PATH, STAGING_PATH, BIN_SIZE, MAX_FILE_SIZE, CERTIFICATE, PackConfig.MODE_PACK)
    pack(config)

@pytest.mark.order(2)
def test_unpack_medium():
    logging.debug("##### ##### test_unpack_medium ()   ##### #####")
    config = PackConfig(SOURCE_PATH, CAR_PATH, RESTORE_PATH, BIN_SIZE, MAX_FILE_SIZE, PRIVATE_KEY, PackConfig.MODE_UNPACK)
    unpack(config)
