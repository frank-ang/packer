
help:
	echo "Packer makefile"

test_pack:
	python ./packer.py -p -s ./test/source -t /tmp/packer -o ./test/output -b 1000
