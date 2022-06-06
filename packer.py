import argparse, logging, os, shutil
from filecoin_packer.pack import Bin, PackConfig 
from filecoin_packer.pack import bin_source_directory, pack_staging_to_car
from filecoin_packer.pack import unpack_car_to_staging, join_large_files, decrypt_staging_files, combine_files_to_output
from multiprocessing import Pool, TimeoutError
from multiprocessing_logging import install_mp_handler #, uninstall_mp_handler
from pathlib import Path


BIN_SIZE_DEFAULT=32000000000 # just under 32GB
FILE_MAX_SIZE_DEFAULT=1024*1024*1024 # 1GB
JOB_CONCURRENCY_DEFAULT=1


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='PROG', 
        description='Filecoin filesystem packager/unpackager',
        usage='python packer.py [--pack|--unpack] [-s SOURCE_PATH] [-t TEMP_PATH] [-o OUTPUT_PATH] [-b BIN_SIZE] [-k ENCRYPTION_KEY]',
        epilog="Alpha version.")
    # group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-p', '--pack', action="store_true", default=False, help='Pack mode')
    parser.add_argument('-u', '--unpack', action="store_true", default=False, help='Unpack mode')
    parser.add_argument('-s', '--source', required=True, help='In Pack mode, the path to the original source data. In Unpack mode, the path containing CAR files.')
    # TODO, staging storage space requires >1x source data size. TODO: Implent CAR-by-CAR micro-batching to reduce staging space requirements.
    parser.add_argument('-t', '--tmp', required=True, help='Path to temporary staging directory. Currently, required temp size > 1x of source data size.')
    parser.add_argument('-o', '--output', required=True, help='Path to write output of packaged or unpackaged content.')
    parser.add_argument('-k', '--key', required=True, help='RSA Cryptographic Key or Certificate')
    parser.add_argument('-b', '--binsize', required=False, default=BIN_SIZE_DEFAULT, type=int, help='[optional] Bin size bytes (default: {})'.format(BIN_SIZE_DEFAULT))
    parser.add_argument('-m', '--filemaxsize', required=False, default=FILE_MAX_SIZE_DEFAULT, type=int, help='[optional] File max size bytes (default: {})'.format(FILE_MAX_SIZE_DEFAULT))
    parser.add_argument('-j', '--jobs', required=False, default=JOB_CONCURRENCY_DEFAULT, type=int, help='[optional] Job concurrency suggestion (default: {})'.format(JOB_CONCURRENCY_DEFAULT))

    return parser


def main() -> None:
    parser = init_argparse()
    parsed_args = parser.parse_args()
    total_size = sum(f.stat().st_size for f in Path(parsed_args.source).glob('**/*') if f.is_file())
    job_bin_size_target = total_size / parsed_args.jobs
    logging.debug("total_size:{} / job count:{} = job_bin_size_target:{} ; ".format(total_size, parsed_args.jobs, job_bin_size_target))

    with os.scandir(parsed_args.source) as iterator:
        children = list(iterator)
    children.sort(key= lambda x: x.name)

    job_bin_size = 0
    job_to_paths_list = [[]]
    for child_path in children:

        if child_path.is_file():
            child_size = child_path.stat().st_size
        elif child_path.is_dir():
            child_size = sum(f.stat().st_size for f in Path(child_path.path).glob('**/*') if f.is_file())
        else:
            raise Exception("Entry is not dir or file type.")
        logging.debug("## path: {} , size:{}".format(child_path.path, child_size))
        if (job_bin_size > 0) and ((job_bin_size + child_size) > job_bin_size_target):
            # child belongs in the next bin
            logging.debug("## next bin")
            job_bin_size = 0
            job_to_paths_list.append([])
        job_bin_size += child_size 
        job_to_paths_list[-1].append(child_path.path)
        logging.debug("##  job bin size: {}".format(job_bin_size))
        logging.debug("##  job_to_paths_list: {}".format(job_to_paths_list))

    # Multiprocessing pool
    install_mp_handler()
    pool = Pool(parsed_args.jobs, initializer=install_mp_handler)
    job_index = 0
    for child_path in job_to_paths_list:
        logging.debug("## Launching job: {}, for paths_list: {}".format(job_index, child_path))
        mode = None
        if parsed_args.pack:
            mode = PackConfig.MODE_PACK
        elif parsed_args.unpack:
            mode = PackConfig.MODE_UNPACK
        else:
            raise Exception("Pack or Unpack parameter required.") 
        zero_padding_digits = len(str(len(job_to_paths_list)))
        job_path_suffix = "JOB.{}".format(str(job_index).zfill(zero_padding_digits))
        job_staging = os.path.join(os.path.normpath(parsed_args.tmp), job_path_suffix) # subdir per-job
        job_config = PackConfig(parsed_args.source, parsed_args.output, job_staging,
                                parsed_args.binsize, parsed_args.filemaxsize,
                                parsed_args.key, mode, job_index)
        pool.apply_async(execute, args=(job_config, child_path))
        job_index += 1
    logging.debug("## all jobs launched.")
    pool.close()
    pool.join()
    logging.debug("## all jobs completed.")
    # Exit.


def execute(config, paths_list) -> None:
    logging.debug("#### Executing Job. PackConfig:{} , Paths:{}".format(vars(config), paths_list))
    if config.mode == config.MODE_PACK:
        logging.debug("#### packing: {}".format(paths_list))
        pack(config, paths_list)
    elif config.mode == config.MODE_UNPACK:
        logging.debug("#### unpacking: {}".format(paths_list))
        unpack(config, paths_list) # , final_output_path)


def pack(config, paths_list) -> None:
    # Pack up the source directory for transport into Filecoin via CAR format.
    logging.debug("## Packing Source: {} ; Paths List: {}".format(config.source_path, paths_list))

    try:

        # 1. Pack the source directory into binned staging directories. Split large files. Encrypt files.
        bin_list = [Bin(0)]

        for child_path in paths_list:
            bin_source_directory(child_path, config, bin_list)

        # cleanup. 
        logging.debug("cleaning up encryption temp dir: {}".format(os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR)))
        shutil.rmtree(os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR), ignore_errors=True)

        # 2. Pack the staging directories into CAR files into output directory.
        pack_staging_to_car(config)
        logging.debug("ID of last bin: {}".format(bin_list[-1].bin_id))

    except Exception as e:
        logging.error(e)
        raise


def unpack(config, paths_list) -> None:
    # Pack up the paths_list directories of CAR files into the output, with extraction and reassembly.
    try:
        # 1. Unpack the CAR files to binned staging directories.
        logging.debug("#>>> unpack_car_to_staging(). paths_list:{}".format(paths_list))

        for child_path in paths_list:
            unpack_car_to_staging(config, child_path)

        # 2. Decrypt files.
        logging.debug("#>>> decrypt_staging_files(). staging_consolidation_path:{}".format(config.staging_consolidation_path))
        decrypt_staging_files(config, config.staging_consolidation_path)

        # 3. Join split file parts into original large files.
        logging.debug("#>>> join_large_files().")
        join_large_files(config)

        # 4. Combine the binned staging directories to the output path.
        logging.debug("#>>> combine_files_to_output().")
        combine_files_to_output(config)

    except Exception as e:
        logging.error(e)
        raise


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.DEBUG) # TODO raise to INFO default, with verbose option.
    main()
