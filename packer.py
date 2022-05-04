import argparse
import logging
from filecoin_packer.pack import Bin, PackConfig 
from filecoin_packer.pack import bin_source_directory, pack_staging_to_car
from filecoin_packer.pack import unpack_car_to_staging, join_large_files, combine_files_to_output

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='PROG', 
        description='Filecoin filesystem packager/unpackager',
        usage='python packer.py [-p|-u] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-e TODO]',
        epilog="Alpha version.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--pack', action=argparse.BooleanOptionalAction, help='Pack mode')
    group.add_argument('-u', '--unpack', action=argparse.BooleanOptionalAction, help='Unpack mode')
    parser.add_argument('-s', '--source', required=True, help='During packing, the path to the pre-packed source data. During unpacking, the path containing CAR files of packed data.')
    parser.add_argument('-t', '--tmp', required=True, help='Path to temporary working directory. (optional)')
    parser.add_argument('-o', '--output', required=True, help='Path to write output of packaged or unpackaged content.')
    parser.add_argument('-b', '--binsize', default=1000, type=int, help='Bin size (bytes)')
    parser.add_argument('--filemaxsize', default=1000, type=int, help='File max size (bytes)')
    # TODO encryption keys parameter.
    return parser

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
    print(args)

    source_path = args.source
    output_path = args.output
    tmp_path = args.tmp
    binsize = args.binsize
    filemaxsize = args.filemaxsize

    if args.pack:
        # Pack up the source directory for transport into Filecoin via CAR format.
        logging.info("Start packing. Args: {}".format(args.pack))
        logging.debug("Scanning Path:" + source_path)

        try:
            config = PackConfig(source_path, output_path, tmp_path, binsize, filemaxsize)
            bin_list = [Bin(0)]
            # 1. Pack the source directory into binned staging directories.
            bin_source_directory(source_path, config, bin_list)

            # 2. TODO: Encrypt the staging directories.?
            # cryptography here, or inside step 1?

            # 3. Pack the staging directories into CAR files into output directory.
            pack_staging_to_car(tmp_path, config)

            logging.debug("ID of last bin: {}".format(bin_list[-1].bin_id))
        except Exception as e:
            logging.debug(e)
            raise

    elif args.unpack:
        # Pack up the source directory of CAR files into the output, with extraction and reassembly.
        logging.info("Start unpacking. Args: {}".format(args.pack))
        try:
            config = PackConfig(source_path, output_path, tmp_path, binsize, filemaxsize)
            # 1. Unpack the CAR files to binned staging directories.
            unpack_car_to_staging(source_path, config)

            # 2. Join split file parts into original large files.
            join_large_files(config)

            # 3. TODO decrypt files.

            # 4. Combine the binned staging directories to the output path.
            combine_files_to_output(config)

        except Exception as e:
            logging.debug(e)
            raise
main()
