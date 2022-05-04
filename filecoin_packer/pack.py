import os,re, logging, shutil, glob
from pickle import TRUE
from subprocess import check_output, STDOUT
from collections import defaultdict
from filecoin_packer.crypt import encrypt, decrypt

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class PackConfig:
    bin_max_bytes = 100
    file_max_bytes = 50
    source_path = "."
    output_path = "."
    tmp_path = "."
    exclude_patterns = ""
    STAGING_CONSOLIDATION_SUBDIR = "TEMP_STAGING"
    staging_consolidation_path = ""

    def __init__(self, source_path, output_path, tmp_path, bin_max_bytes, file_max_bytes):
        self.source_path = source_path
        self.output_path = output_path
        self.tmp_path = tmp_path
        self.staging_consolidation_path = "{}/{}/".format(os.path.abspath(self.tmp_path), self.STAGING_CONSOLIDATION_SUBDIR)
        self.bin_max_bytes = bin_max_bytes
        self.file_max_bytes = file_max_bytes
        self.exclude_patterns = [".DS_Store"]

class Bin:
    bin_id = 0
    bin_size = 0
    def __init__(self, bin_id):
        self.bin_id = bin_id
        self.bin_size = 0
    def add(self, filesize):
        self.bin_size += filesize
        return self.bin_size
    def bin_name(self):
        return "CAR{}".format(self.bin_id)

def handle_large_file(filepath, config, bin_list):
    """
    split orig
    for pieces:
        if piece.size + bin.size > config.bin_max_bytes:
            increment new bin.
        bin.add(piece.size)
        move piece
    """
    logging.info("splitting large file. {}".format(filepath))
    cur_bin = bin_list[-1]
    file_number = 1
    with open(filepath) as orig:
        # TODO change to buffered reads and buffered writes to handle super large files.
        chunk = orig.read(config.file_max_bytes)
        while chunk:

            path_in_car = os.path.relpath(os.path.dirname(filepath), config.source_path)
            staging_chunkname = "{}/{}.split.{}".format(path_in_car, os.path.basename(filepath), file_number)
            staging_chunkname = os.path.join(config.tmp_path,
                                cur_bin.bin_name(),
                                staging_chunkname)
            staging_chunkname = os.path.normpath(staging_chunkname)

            os.makedirs(os.path.dirname(staging_chunkname), exist_ok=TRUE)
            logging.debug("# writing chunk to: {}".format(staging_chunkname))
            with open(staging_chunkname, "w") as staging_file:
                staging_file.write(chunk)
            file_number += 1
            chunk_bytes = len(chunk)

            # Encrypt.
            encrypt(staging_chunkname, config)

            # Note, split chunks of a large file may span multiple bins.
            # TODO use the encrypted file's size if available.
            if (cur_bin.bin_size + chunk_bytes) > config.bin_max_bytes:
                logging.debug("++Bin Increment! {} + {} > {}".format(cur_bin.bin_size, chunk_bytes, config.bin_max_bytes))
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(chunk_bytes)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(chunk_bytes)
            logging.debug("Bin:{}, BinSize:{}, Path:{} :FileSize:{}".format(
                cur_bin.bin_id, cur_bin.bin_size, staging_chunkname, chunk_bytes))
            chunk = orig.read(config.file_max_bytes)


def bin_source_directory(path, config, bin_list):
    """
    Processes the specified source path, 
    copying files into maximum-sized bins of subdirectories within the destination path.
    Features:
    * Large file splitting. (current MVP)
    * Encryption. (TODO implement)
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
            # File

            # Skip excluded files
            # Using join regex + loop + re.match()
            pattern = '(?:% s)' % '|'.join(config.exclude_patterns)
            if re.match(pattern, entry.name):
                continue

            file_size = entry.stat().st_size

            # 1. Split large files, process each of the pieces. 
            if file_size > config.file_max_bytes:
                handle_large_file(entry.path, config, bin_list)
                continue

            # 2. Encrypt files. 
            encrypt(entry.path, config)

            if (cur_bin.bin_size + file_size) > config.bin_max_bytes:
                logging.debug("++Bin Increment! {} + {} > {}".format(cur_bin.bin_size, file_size, config.bin_max_bytes))
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(file_size)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(file_size)
            logging.debug("Bin:{}, BinSize:{}, Path:{} :FileSize:{}".format(
                cur_bin.bin_id, cur_bin.bin_size, entry.path, file_size))
            file_staging_path = os.path.join(config.tmp_path,
                                cur_bin.bin_name(), 
                                os.path.relpath(entry.path,config.source_path))
            file_staging_path = os.path.normpath(file_staging_path)
            logging.debug("... copy to output: {}".format(file_staging_path))
            os.makedirs(os.path.dirname(file_staging_path), exist_ok=TRUE)
            shutil.copyfile(entry.path, file_staging_path)

        elif entry.is_dir():
            # Directory
            bin_source_directory(entry.path, config, bin_list)
            # subdirectories may have added new bins
        else:
            raise Exception("Entry is not dir or file type.")


def pack_staging_to_car(path, config):
    """
    Processes the specified staging path, 
    copying files into maximum-sized bins of subdirectories within the destination path.
    Features:
    * Large file splitting. (current MVP)
    * Encryption. (TODO implement)
    Parameters:
        path: Path of source filesystem.
        config: switches
        bin_list: Processing state maintained in a list of Bin objects.
    """
    logging.debug("# pack_staging_to_car(): path:{}".format(path))

    with os.scandir(path) as iterator:
        children = list(iterator)
    children.sort(key= lambda x: x.name)
    output_dir_path = os.path.normpath(config.output_path)
    os.makedirs(output_dir_path, exist_ok=TRUE)
    for car_directory in children:
        logging.debug("# packing car from staging bin: {}".format(car_directory.path))
        ipfs_car_cmd = "ipfs-car --pack {} --output {}.car".format(car_directory.path, 
            os.path.join(output_dir_path,os.path.basename(car_directory.path)))
        logging.debug("# CAR executing: {}".format(ipfs_car_cmd))
        cmd_out = check_output(ipfs_car_cmd, stderr=STDOUT, shell=True)
        logging.debug("# CAR returns: {}".format(cmd_out))


def unpack_car_to_staging(path, config):
    """
    Unpacks a bunch of CAR files in a source directory, into a staging directory.
    """
    CAR_SUFFIX=".car"
    logging.debug("# unpack_car_to_staging(). path:{}".format(path))
    with os.scandir(path) as iterator:
        children = list(iterator)
    children.sort(key= lambda x: x.name)
    # Filter only matching ".car" files
    staging_dir_path = os.path.normpath(config.tmp_path)
    os.makedirs(staging_dir_path, exist_ok=TRUE)

    for car_file in children:
        if not car_file.name.endswith(CAR_SUFFIX):
            continue

        ipfs_car_cmd = "ipfs-car --unpack {} --output {}".format(car_file.path, staging_dir_path) 
        logging.debug("# Unpack CAR executing: {}".format(ipfs_car_cmd))
        cmd_out = check_output(ipfs_car_cmd, stderr=STDOUT, shell=True)

    # Move all staging CAR subdirs into the same root dir.
    staging_dir = os.path.abspath(os.path.normpath(config.tmp_path))
    CAR_SUBDIR_CONTENT_PATTERN = "CAR[0-9]*/"
    car_content_paths = sorted(glob.glob(CAR_SUBDIR_CONTENT_PATTERN, root_dir=staging_dir, recursive=False)) 
    consolidated_staging_dir_path = config.staging_consolidation_path
    os.makedirs(consolidated_staging_dir_path, exist_ok=TRUE)

    for bin_dir in car_content_paths:
        bin_dir = os.path.normpath(os.path.join(staging_dir_path,bin_dir)) + "/"
        logging.debug("# moving from:{}, to:{}".format(bin_dir, consolidated_staging_dir_path))
        move_cmd = "rsync -a {} {}".format(bin_dir, consolidated_staging_dir_path) 
        logging.debug("# Moving bin directory, executing: {}".format(move_cmd))
        cmd_out = check_output(move_cmd, stderr=STDOUT, shell=True)

def join_large_files(config):
    logging.debug("# join_large_files()")
    SPLIT_FILE_PATTERN = "**/*.split.[0-9]*"
    split_file_paths = sorted(glob.glob(SPLIT_FILE_PATTERN, root_dir=config.staging_consolidation_path, recursive=True))
    logging.info("## split_file_paths: {}".format(split_file_paths))
    large_file_map = defaultdict(list)
    # Find all the part files for each split file.
    for part_file_path in split_file_paths:
        # Extract the original filename from the part file.
        logging.debug("## part_file_path (1): {}".format(part_file_path))
        LARGE_FILENAME_REGEX = "(.+?)\.split\.[0-9]+?"
        large_filename = re.search(LARGE_FILENAME_REGEX, part_file_path).group(1)
        large_filename = os.path.normpath(os.path.join(config.staging_consolidation_path, large_filename))
        part_file_path = os.path.normpath(os.path.join(config.staging_consolidation_path, part_file_path))
        logging.debug("## part_file_path (2): {}".format(part_file_path))
        large_file_map[large_filename].append(part_file_path)
    # Join the parts
    for large_filename in large_file_map:
        logging.debug("# joining {} from parts: {}".format(large_filename, large_file_map[large_filename]))
        # Bufferred Join.
        BLOCKSIZE = 4096
        BLOCKS = 1024
        chunk = BLOCKS * BLOCKSIZE
        with open(large_filename, "w+b") as outfile:
            for part_file_path in large_file_map[large_filename]:
                with open(part_file_path, "rb") as infile:
                    outfile.write(infile.read(chunk))
                os.remove(part_file_path)

def combine_files_to_output(config):
    logging.debug("# combine_files_to_output()")
    staging_dir = os.path.abspath(os.path.normpath(config.staging_consolidation_path)) + "/"
    output_dir_path = os.path.abspath(config.output_path) + "/"
    os.makedirs(output_dir_path, exist_ok=TRUE)

    logging.debug("# moving from:{}, to:{}".format(staging_dir, output_dir_path))
    move_cmd = "rsync -a {} {}".format(staging_dir, output_dir_path) 
    logging.debug("# Moving bin directory, executing: {}".format(move_cmd))
    cmd_out = check_output(move_cmd, stderr=STDOUT, shell=True)

'''
    for bin_dir in staging_content_paths:
        bin_dir = os.path.normpath(os.path.join(staging_dir,bin_dir)) + "/"
        logging.debug("# moving from:{}, to:{}".format(bin_dir, output_dir_path))
        move_cmd = "rsync -a {} {}".format(bin_dir, output_dir_path) 
        logging.debug("# Moving bin directory, executing: {}".format(move_cmd))
        cmd_out = check_output(move_cmd, stderr=STDOUT, shell=True)
'''