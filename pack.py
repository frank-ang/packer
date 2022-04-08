import os,sys

def handle_directory(base_path, depth_string):
    with os.scandir(path=base_path) as children:
        total_bytes=0
        for entry in children:
            if entry.is_file():
                # File
                total_bytes += entry.stat().st_size
                print(depth_string + entry.name + ":" + str(entry.stat().st_size))
                # print("size:" + str(entry.stat().st_size))
            elif entry.is_dir():
                # Directory
                print(depth_string+'#'+entry.name)
                total_bytes += handle_directory(entry.path, depth_string+'-->')
                # TODO... need a return value.
                # e.g. total += handle_directory()
                #   return total... ??
            else:
                print ("OTHER!")
        return total_bytes

k=''
base_path="/Users/frankang/lab/packer/test" # "./test/origin" # TODO: fix Hardcoding
print('Scanning Path:' + base_path)
try:
    total_bytes=handle_directory(base_path,k)
    print("TOTAL size bytes:"+str(total_bytes))
except Exception as e:
    print(e)
    raise