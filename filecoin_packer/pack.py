from doctest import UnexpectedException
import os,re, logging
# from unicodedata import name

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class PackConfig:
    bin_max_bytes = 100
    file_max_bytes = 50
    source_path = "."
    output_path = "."
    tmp_path = "."
    exclude_patterns = ""
    def __init__(self, source_path, output_path, tmp_path, bin_max_bytes):
        self.source_path = source_path
        self.output_path = output_path
        self.tmp_path = tmp_path
        self.bin_max_bytes = bin_max_bytes
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

def handle_large_file(path, config, bin_list):
    ''' 
    split orig
    for pieces:
        if piece.size + bin.size > config.bin_max_bytes:
            increment new bin.
        bin.add(piece.size)
        move piece
    '''
    logging.info("splitting large file. {}".format(path))
    cur_bin = bin_list[-1]
    file_number = 1
    with open(path) as orig:
        chunk = orig.read(config.file_max_bytes)
        while chunk:
            target_filename = "{}/{}.split.{}".format(os.path.dirname(path),os.path.basename(path), file_number)
            with open(target_filename, "w") as target_file:
                target_file.write(chunk)
            file_number += 1
            chunk_bytes = len(chunk)
            # Note, split chunks of a large file may span multiple bins.
            if (cur_bin.bin_size + chunk_bytes) > config.bin_max_bytes:
                logging.debug("++Bin Increment! {} + {} > {}".format(cur_bin.bin_size, chunk_bytes, config.bin_max_bytes))
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(chunk_bytes)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(chunk_bytes)
            logging.debug("Bin:{}, BinSize:{}, Path:{} :FileSize:{}".format(
                cur_bin.bin_id, cur_bin.bin_size, target_filename, chunk_bytes))
            file_output_path = os.path.join(config.output_path, 
                                cur_bin.bin_name(), 
                                os.path.relpath(target_filename,config.output_path))
            file_output_path = os.path.normpath(file_output_path)
            logging.debug("... move to staging: {}".format(file_output_path))

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
        config: switches
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

            # 1. Split large files. 
            if file_size > config.file_max_bytes:
                handle_large_file(entry.path, config, bin_list)
                continue

            # TODO
            # 2. Encrypt files. 


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
            file_output_path = os.path.join(config.output_path, 
                                cur_bin.bin_name(), 
                                os.path.relpath(entry.path,config.source_path))
            file_output_path = os.path.normpath(file_output_path)
            logging.debug("... copy to output: {}".format(file_output_path))

        elif entry.is_dir():
            # Directory
            bin_source_directory(entry.path, config, bin_list)
            # subdirectories may have added new bins
        else:
            raise UnexpectedException("Entry is not dir or file type.")


def pack_staging_to_car(path, config, bin_list):
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
    logging.debug("# pack_staging_to_car()")