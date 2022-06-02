import argparse
from filecoin_packer.pack import PackConfig 
from filecmp import dircmp
import logging
from os import path
from packer import JOB_CONCURRENCY_DEFAULT, pack, unpack, main
import pytest
from shutil import rmtree
from subprocess import CalledProcessError, check_output, STDOUT
from unittest import mock


SOURCE_PATH="./test/source"
LARGE_DATA_PATH="./test/large-source"
STAGING_PATH="./test/staging"
CAR_PATH="./test/car"
RESTORE_PATH="./test/restore"
JOB_CONCURRENCY=2

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


@pytest.mark.order(10)
@mock.patch('argparse.ArgumentParser.parse_args',
            return_value=argparse.Namespace(pack=True,
                                            source=SOURCE_PATH,
                                            tmp=STAGING_PATH,
                                            output=CAR_PATH,
                                            binsize=BIN_SIZE,
                                            filemaxsize=MAX_FILE_SIZE,
                                            key=CERTIFICATE,
                                            jobs=JOB_CONCURRENCY))
def test_pack_command(mock_args):
    try:
        rmtree(STAGING_PATH, ignore_errors=True)
        rmtree(CAR_PATH, ignore_errors=True)
        main()
    except TypeError as e:
        logging.debug("caught exception: {}".format(e))


@pytest.mark.order(11)
@mock.patch('argparse.ArgumentParser.parse_args',
            return_value=argparse.Namespace(pack=False,
                                            unpack=True,
                                            source=CAR_PATH,
                                            tmp=STAGING_PATH,
                                            output=RESTORE_PATH,
                                            binsize=BIN_SIZE,
                                            filemaxsize=MAX_FILE_SIZE,
                                            key=PRIVATE_KEY,
                                            jobs=JOB_CONCURRENCY))
def test_unpack_command(mock_args):
    rmtree(STAGING_PATH, ignore_errors=True)
    rmtree(RESTORE_PATH, ignore_errors=True)
    try:
        main()
    except TypeError as e:
        logging.debug("caught exception: {}".format(e))
    assertSame(SOURCE_PATH, RESTORE_PATH)



def assertSame(dir1, dir2):
    logging.debug("assertSame({}, {})".format(dir1,dir2))
    dcmp = dircmp(dir1, dir2)
    assert len(dcmp.diff_files) == 0 , "directories differ: {}".format(dcmp.diff_files)
