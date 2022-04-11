from doctest import UnexpectedException
import os,re, logging
from unicodedata import name

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class PackConfig:
    bin_max_bytes = 100
    base_path = "."
    staging_path = "./staging"
    exclude_patterns = ""
    def __init__(self, base_path, staging_path):
        self.base_path = base_path
        self.staging_path = staging_path
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

def handle_directory(path, config, bin_list):

    cur_bin = bin_list[-1]
    logging.debug("# handle_directory(): path:{}, bin:{}".format(path, cur_bin.bin_id))

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

            # TODO:
            # 1. Split large files. 
            # 2. Encrypt files. 
            # 3. Detect when max size is reached, change to new target base dir.
            # 4. Move files to target base.
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
            file_staging_path = os.path.join(config.staging_path, 
                                cur_bin.bin_name(), 
                                os.path.relpath(entry.path,config.base_path))
            file_staging_path = os.path.normpath(file_staging_path)
            logging.debug("... copy to staging: {}".format(file_staging_path))

        elif entry.is_dir():
            # Directory
            handle_directory(entry.path, config, bin_list)
            # subdirectories may have added new bins
        else:
            raise UnexpectedException("Entry is not dir or file type.")

base_path="./test/origin" # TODO: fix Hardcoding
staging_path="./test/staging"  # TODO: fix Hardcoding
logging.debug("Scanning Path:" + base_path)
try:
    config = PackConfig(base_path, staging_path)
    bin_list = [Bin(0)]
    handle_directory(base_path, config, bin_list)
    logging.debug("ID of last bin: {}".format(bin_list[-1].bin_id))
except Exception as e:
    logging.debug(e)
    raise