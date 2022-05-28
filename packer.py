import argparse, logging, os, shutil
from filecoin_packer.pack import Bin, PackConfig 
from filecoin_packer.pack import bin_source_directory, pack_staging_to_car
from filecoin_packer.pack import unpack_car_to_staging, join_large_files, decrypt_staging_files, combine_files_to_output

BIN_SIZE_DEFAULT=32000000000
FILE_MAX_SIZE_DEFAULT=1024*1024*1024

logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.DEBUG)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='PROG', 
        description='Filecoin filesystem packager/unpackager',
        usage='python packer.py [--pack|--unpack] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-k ENCRYPTION_KEY]',
        epilog="Alpha version.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--pack', action=argparse.BooleanOptionalAction, help='Pack mode')
    group.add_argument('-u', '--unpack', action=argparse.BooleanOptionalAction, help='Unpack mode')
    parser.add_argument('-s', '--source', required=True, help='During packing, the path to the original source data. During unpacking, the path containing CAR files.')
    parser.add_argument('-t', '--tmp', required=True, help='Path to temporary staging directory.')
    parser.add_argument('-o', '--output', required=True, help='Path to write output of packaged or unpackaged content.')
    parser.add_argument('-b', '--binsize', required=False, default=BIN_SIZE_DEFAULT, type=int, help='Bin size (bytes)')
    parser.add_argument('-m', '--filemaxsize', required=False, default=FILE_MAX_SIZE_DEFAULT, type=int, help='File max size (bytes)')
    parser.add_argument('-k', '--key', required=False, help='Cryptographic Key or Certificate')
    return parser

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
    config = PackConfig(args.source, args.output, args.tmp, args.binsize, args.filemaxsize, args.key)
    logging.debug("PackConfig: {}".format(vars(config)))
    if args.pack:
        pack(config)
    elif args.unpack:
        unpack(config)


def pack(config) -> None:
    # Pack up the source directory for transport into Filecoin via CAR format.
    logging.debug("Scanning Path:" + config.source_path)
    try:
        bin_list = [Bin(0)]

        # 1. Pack the source directory into binned staging directories. Split large files. Encrypt files.
        bin_source_directory(config.source_path, config, bin_list)

        # cleanup. 
        logging.debug("cleaning up encryption temp dir: {}".format(os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR)))
        shutil.rmtree(os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR), ignore_errors=True)

        # 2. Pack the staging directories into CAR files into output directory.
        pack_staging_to_car(config)
        logging.debug("ID of last bin: {}".format(bin_list[-1].bin_id))

    except Exception as e:
        logging.debug(e)
        raise


def unpack(config) -> None:
    # Pack up the source directory of CAR files into the output, with extraction and reassembly.
    try:
        # 1. Unpack the CAR files to binned staging directories.
        unpack_car_to_staging(config)

        # 2. Decrypt files.
        decrypt_staging_files(config.staging_consolidation_path, config)

        # 3. Join split file parts into original large files.
        join_large_files(config)

        # 4. Combine the binned staging directories to the output path.
        combine_files_to_output(config)

    except Exception as e:
        logging.debug(e)
        raise


if __name__ == "__main__":
    main()
