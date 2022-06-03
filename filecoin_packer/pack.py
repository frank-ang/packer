import glob, logging, os, re, shutil
from collections import defaultdict
from tokenize import Binnumber
from filecoin_packer.crypt import encrypt, decrypt
from math import ceil
from multiprocessing_logging import install_mp_handler
from pickle import TRUE
from subprocess import CalledProcessError, check_output, STDOUT

FILE_READ_BUFFER_SIZE = 1024 * 1024

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.DEBUG) # TODO raise to INFO default, with verbose option.

class PackConfig:

    bin_max_bytes = None
    file_max_bytes = None
    source_path = "."
    staging_base_path = "."
    STAGING_ENCRYPTION_SUBDIR = "TEMP_ENCRYPT"
    STAGING_CONSOLIDATION_SUBDIR = "TEMP_STAGING"
    staging_consolidation_path = ""
    output_path = "."
    exclude_patterns = ""
    ENCRYPTED_FILE_SUFFIX = ".encrypted"
    key_path = None
    mode = None
    MODE_PACK = "MODE_PACK"
    MODE_UNPACK = "MODE_UNPACK"
    job_id = None

    @classmethod
    def from_args(cls, args, job_id=1):
        return cls(args.source_path, args.output_path, args.staging_base_path, args.binsize, args.args.filemaxsize, args.key, args.mode, job_id)

    def __init__(self, source_path, output_path, staging_base_path, bin_max_bytes, file_max_bytes, key_path, mode, job_id=1):
        self.source_path = source_path
        self.output_path = output_path
        self.staging_base_path = staging_base_path
        self.staging_consolidation_path = "{}/{}/".format(os.path.abspath(self.staging_base_path), self.STAGING_CONSOLIDATION_SUBDIR)
        self.bin_max_bytes = bin_max_bytes
        self.file_max_bytes = file_max_bytes
        self.exclude_patterns = [".DS_Store"]
        self.key_path = key_path
        self.mode = mode
        self.job_id = job_id


class Bin:
    bin_id = 0
    bin_size = 0
    def __init__(self, bin_id):
        self.bin_id = bin_id
        self.bin_size = 0
    def add(self, filesize):
        self.bin_size += filesize
        return self.bin_size
    def bin_name(self, job_id):
        return "JOB{}-CAR{}".format(job_id, self.bin_id)


def bin_source_directory(path, config, bin_list) -> None:
    """
    Traverse the specified path, 
    copy files into maximum-sized bins of subdirectories under the config staging path.
    Features:
    * Large file splitting.
    * Encryption.
    Parameters:
        path: Path of source filesystem.
        config: parameters
        bin_list: Processing state maintained in a list of Bin objects.
    """

    cur_bin = bin_list[-1]
    logging.debug("# bin_source_directory(): path:{}, bin:{}".format(path, cur_bin.bin_id))

    with os.scandir(path) as iterator:
        children = list(iterator)
    children.sort(key= lambda x: x.name)

    for entry in children:
        if entry.is_file():
            # Skip excluded files
            # Using join regex + loop + re.match()
            pattern = '(?:% s)' % '|'.join(config.exclude_patterns)
            if re.match(pattern, entry.name):
                continue

            file_size = entry.stat().st_size

            # 1. Split large files, process each of the pieces. 
            if file_size > config.file_max_bytes:
                pack_large_file_to_staging(entry.path, config, bin_list)
                continue

            file_to_pack = entry.path
            relpath = os.path.relpath(file_to_pack, config.source_path)

            # 2. Encrypt file. TODO conditional encryption based on switch (existence of config.key_path parameter)
            encrypted_file_path = os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR, relpath + config.ENCRYPTED_FILE_SUFFIX)
            os.makedirs(os.path.dirname(encrypted_file_path), exist_ok=TRUE)
            encrypted_file_path = encrypt(entry.path, encrypted_file_path, config)

            if not encrypted_file_path is None:
                file_size = os.path.getsize(encrypted_file_path)
                file_to_pack = encrypted_file_path
                relpath = os.path.relpath(file_to_pack, os.path.join(config.staging_base_path, config.STAGING_ENCRYPTION_SUBDIR))

            # Determine which Bin.
            if (cur_bin.bin_size + file_size) > config.bin_max_bytes:
                logging.debug("++Bin Increment! {} + {} > {}".format(cur_bin.bin_size, file_size, config.bin_max_bytes))
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(file_size)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(file_size)
            logging.debug("Bin:{}, BinSize:{}, Path:{} :FileSize:{}".format(
                cur_bin.bin_id, cur_bin.bin_size, file_to_pack, file_size))
            file_staging_path = os.path.normpath(os.path.join(config.staging_base_path,
                                cur_bin.bin_name(config.job_id), relpath))
            os.makedirs(os.path.dirname(file_staging_path), exist_ok=TRUE)
            # If encrypted, move to staging. If not encrypting, copy to staging.
            if not encrypted_file_path is None:
                logging.debug("... move encrypted file to output: {}".format(file_staging_path))
                shutil.move(file_to_pack, file_staging_path)
            else:
                logging.debug("... copy file to output: {}".format(file_staging_path))
                shutil.copyfile(file_to_pack, file_staging_path)

        elif entry.is_dir():
            # Recurse into directory. New bins to be created accordingly.
            bin_source_directory(entry.path, config, bin_list)
        else:
            raise Exception("Entry is not dir or file type.")


def pack_large_file_to_staging(filepath, config, bin_list) -> None:
    """
    Split large file, move to staging, encrypt. Simple lexical bin-packing.
    """
    cur_bin = bin_list[-1]
    file_number = 1
    num_chunks = ceil(os.path.getsize(filepath) / config.file_max_bytes)
    chunk_length_digits = len(str(ceil(num_chunks))) 
    logging.info("splitting large file: {} , into number of chunks: {}".format(filepath, num_chunks))

    with open(filepath, mode='rb') as orig:

        chunk_fragment = orig.read(FILE_READ_BUFFER_SIZE)
        chunk_bytes = 0
        chunk_write_bytes = 0
        while chunk_fragment:
            path_in_car = os.path.relpath(os.path.dirname(filepath), config.source_path)
            staging_chunkname = os.path.normpath(os.path.join(
                                    config.staging_base_path,
                                    cur_bin.bin_name(config.job_id),
                                    "{}/{}.split.{}".format(
                                        path_in_car,
                                        os.path.basename(filepath),
                                        str(file_number).zfill(chunk_length_digits))))
            os.makedirs(os.path.dirname(staging_chunkname), exist_ok=TRUE)
            logging.debug("# writing chunk to: {}".format(staging_chunkname))
            with open(staging_chunkname, "ab") as staging_file:
                while (chunk_fragment) and (chunk_write_bytes <= config.file_max_bytes): 
                    chunk_write_bytes += staging_file.write(chunk_fragment)
                    chunk_fragment = orig.read(FILE_READ_BUFFER_SIZE)
                # End of Chunk.

            file_number += 1
            chunk_bytes += chunk_write_bytes

            # Encrypt chunk.
            encrypted_file_path = encrypt(staging_chunkname, None, config)
            if not encrypted_file_path is None:
                # Remove unencrypted staging chunk.
                os.remove(staging_chunkname)
                chunk_bytes = os.path.getsize(encrypted_file_path)

            # Note, split chunks of a large file may span multiple bins.
            if (cur_bin.bin_size + chunk_bytes) > config.bin_max_bytes:
                logging.debug("++Bin Increment! {} + {} > {}".format(cur_bin.bin_size, chunk_bytes, config.bin_max_bytes))
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(chunk_bytes)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(chunk_bytes)
            chunk_write_bytes = 0


def pack_staging_to_car(config) -> None:
    """
    Processes the specified staging path, 
    copying files into maximum-sized bins of subdirectories within the destination path.
    """
    logging.debug("# pack_staging_to_car(): path:{}".format(config.staging_base_path))

    with os.scandir(config.staging_base_path) as iterator:
        children = list(iterator)
    children.sort(key= lambda x: x.name)
    output_dir_path = os.path.normpath(config.output_path)
    os.makedirs(output_dir_path, exist_ok=TRUE)
    for car_directory in children:
        logging.debug("# packing car from staging bin: {}".format(car_directory.path))
        path_to_files = car_directory.path + "/"
        ipfs_car_cmd = "ipfs-car --wrapWithDirectory false --pack {} --output {}.car".format(path_to_files,
            os.path.join(output_dir_path,os.path.basename(car_directory.path)))
        logging.debug("# CAR executing: {}".format(ipfs_car_cmd))
        try:
            cmd_out = check_output(ipfs_car_cmd, stderr=STDOUT, shell=True)
            logging.debug("# CAR completed, output: {}".format(cmd_out))
        except CalledProcessError as e:
            raise Exception(e.output) from e


def unpack_car_to_staging(config, path) -> None:
    """
    Takes a bunch of CAR files from a source directory, and unpacks into the staging directory.
    """
    logging.debug("# unpack_car_to_staging(). path:{}".format(path))
    children = None
    if re.match(r'.*JOB[0-9]*-CAR[0-9]*.car', path):
        # CAR file.
        logging.debug("Found CAR file: {}".format(path));
        children = [path]
    else:
        # Directory.
        CAR_FILE_PATTERN = path + '/**/JOB[0-9]*-CAR[0-9]*.car'
        logging.debug("## CAR_FILE_PATTERN: {}".format(CAR_FILE_PATTERN));
        children = sorted(glob.glob(CAR_FILE_PATTERN, recursive=True))
        logging.debug("Found directory: {}; CAR files inside: {}".format(path, children))

    staging_dir_path = os.path.normpath(config.staging_consolidation_path)
    os.makedirs(staging_dir_path, exist_ok=TRUE)

    for car_file_path in children:
        ipfs_car_cmd = "ipfs-car --unpack {} --output {}".format(car_file_path, staging_dir_path) 
        logging.debug("# Unpack CAR executing: {}".format(ipfs_car_cmd))
        try:
            cmd_out = check_output(ipfs_car_cmd, stderr=STDOUT, shell=True)
        except CalledProcessError as e:
            raise Exception(e.output) from e

    # Move all staging CAR subdirs into the same root dir.
    staging_dir = os.path.abspath(os.path.normpath(config.staging_base_path))
    CAR_SUBDIR_CONTENT_PATTERN = staging_dir + "/CAR[0-9]*/"
    car_content_paths = sorted(glob.glob(CAR_SUBDIR_CONTENT_PATTERN, recursive=False)) 
    os.makedirs(config.staging_consolidation_path, exist_ok=TRUE)

    for bin_dir in car_content_paths:
        bin_dir = os.path.normpath(os.path.join(staging_dir_path,bin_dir)) + "/"
        logging.debug("# moving from:{}, to:{}".format(bin_dir, config.staging_consolidation_path))
        move_cmd = "rsync --remove-source-files -a {} {}".format(bin_dir, config.staging_consolidation_path)
        logging.debug("# Moving bin: {}".format(move_cmd))
        try:
            cmd_out = check_output(move_cmd, stderr=STDOUT, shell=True)
        except CalledProcessError as e:
            raise Exception(e.output) from e


def join_large_files(config) -> None:
    logging.debug("# join_large_files()")
    SPLIT_FILE_PATTERN = config.staging_consolidation_path + "/**/*.split.[0-9]*"
    split_file_paths = sorted(glob.glob(SPLIT_FILE_PATTERN, recursive=True))
    logging.info("## split_file_paths: {}".format(split_file_paths))
    large_file_map = defaultdict(list)
    # Find all the part files for each split file.
    for part_file_path in split_file_paths:
        # Extract the original filename from the part file.
        LARGE_FILENAME_REGEX = "(.+?)\\.split\\.[0-9]+?"
        large_filename = re.search(LARGE_FILENAME_REGEX, part_file_path).group(1)
        large_filename = os.path.normpath(os.path.join(config.staging_consolidation_path, large_filename))
        part_file_path = os.path.normpath(os.path.join(config.staging_consolidation_path, part_file_path))
        logging.debug("## part_file_path: {}".format(part_file_path))
        large_file_map[large_filename].append(part_file_path)
    # Join the parts
    for large_filename in large_file_map:
        logging.debug("# joining {} from parts: {}".format(large_filename, large_file_map[large_filename]))
        with open(large_filename, "wb") as joined_file:
            for part_file_path in large_file_map[large_filename]:
                with open(part_file_path, "rb") as part_file:
                    logging.debug("## writing file part: {}".format(part_file_path))
                    # loop write
                    chunk_fragment = part_file.read(FILE_READ_BUFFER_SIZE)
                    while (chunk_fragment):
                        joined_file.write(chunk_fragment)
                        chunk_fragment = part_file.read(FILE_READ_BUFFER_SIZE)
                # End of Chunk.
                os.remove(part_file_path)


def combine_files_to_output(config) -> None:
    logging.debug("# combine_files_to_output()")
    staging_dir = os.path.abspath(os.path.normpath(config.staging_consolidation_path)) + "/"
    output_dir_path = os.path.abspath(config.output_path) + "/"
    os.makedirs(output_dir_path, exist_ok=TRUE)

    logging.debug("# moving from:{}, to:{}".format(staging_dir, output_dir_path))
    move_cmd = "rsync --remove-source-files -a {} {}".format(staging_dir, output_dir_path) # TODO --remove-source-files
    logging.debug("# Moving bin: {}".format(move_cmd))
    try:
        cmd_out = check_output(move_cmd, stderr=STDOUT, shell=True)
    except CalledProcessError as e:
            raise Exception(e.output) from e


def decrypt_staging_files(config, input_path) -> None:
    """
    Traverse into the directory path and decrypt files in-place.
    """
    logging.debug("## decrypt_staging_files. path: {}".format(input_path))

    if os.path.isfile(input_path):
        # decrypt file
        decrypted_path = decrypt(input_path, config)
        logging.debug("### decrypted {} to: {}".format(input_path, decrypted_path))
        os.remove(input_path) # delete encrypted input file
    elif os.path.isdir(input_path):
        with os.scandir(input_path) as iterator:
            children = list(iterator)
        children.sort(key= lambda x: x.name)
        # logging.debug("### decrypt traversing directory: {}, children: {}".format(input_path, children))
        for entry in children:
            decrypt_staging_files(config, entry.path)
    else:
        raise Exception("encountered non-file and non-directory.")
