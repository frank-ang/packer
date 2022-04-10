from doctest import UnexpectedException
import os,re
from unicodedata import name

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
        print("Bin:{}, size:{}, add:{}".format(self.bin_id, self.bin_size, filesize))
        self.bin_size += filesize
        return self.bin_size
    def bin_name(self):
        return "CAR{}".format(self.bin_id)

def handle_directory(path, config, bin_list):

    cur_bin = bin_list[-1]

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
            print("testing if bin size:{} + filesize:{} > {}".format(cur_bin.bin_size, file_size, config.bin_max_bytes))
            if (cur_bin.bin_size + file_size) > config.bin_max_bytes:
                print("Bin Increment! ", cur_bin.bin_size, "+", file_size, " > ", config.bin_max_bytes)
                next_bin = Bin(cur_bin.bin_id + 1)
                next_bin.add(file_size)
                bin_list.append(next_bin)
                cur_bin=next_bin
            else:
                cur_bin.add(file_size)
            print(entry.path, ":FileSize:", file_size, ", BinSize:", cur_bin.bin_size)
            file_staging_path = os.path.join(config.staging_path, 
                                cur_bin.bin_name(), 
                                os.path.relpath(entry.path,config.base_path))
            file_staging_path = os.path.normpath(file_staging_path)
            print("   ... copy to staging:", file_staging_path)
        elif entry.is_dir():
            # Directory
            print(entry.path, "... directory")
            handle_directory(entry.path, config, bin_list)
            # subdirectories may have added new bins
        else:
            raise UnexpectedException("Entry is not dir or file type.")

base_path="./test/origin" # TODO: fix Hardcoding
staging_path="./test/staging"  # TODO: fix Hardcoding
print('Scanning Path:' + base_path)
try:
    config = PackConfig(base_path, staging_path)
    bin_list = [Bin(0)]
    handle_directory(base_path, config, bin_list)
except Exception as e:
    print(e)
    raise