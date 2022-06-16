#! /bin/bash
. ./packer.conf
echo "📦📦📦📦 Running script: $0 📦📦📦📦"
echo "dumping config..."
echo "  PACK_MODE=$PACK_MODE"
echo "  DATA_SOURCE=$DATA_SOURCE"
echo "  DATA_TARGET=$DATA_TARGET"
echo "  ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "  STAGING_PATH=$STAGING_PATH"
echo "  JOBS=$JOBS"

# Mount Source NFS/S3 as required
# IF NFS then mount; elif S3 then rclone
# Parse DATA_SOURCE for leading protocol. 
# E.g. 
#   NFS pattern: "fs-d1234567.efs.[region].amazonaws.com:/sub0/sub1/"
#   S3 pattern:  "S3://bucket-name/key-name"

export NFS_EXAMPLE_SOURCE="fs-d1234567.efs.[region].amazonaws.com:/sub0/sub1/"
export S3_EXAMPLE_SOURCE="S3://bucket-name/key-name"
export DATA_SOURCE=$S3_EXAMPLE_SOURCE

echo "checking DATA_SOURCE pattern..."

if [[ "$DATA_SOURCE" =~ ^[S|s]3://.+/.* ]]; then
	echo "S3 Data source..."

elif [[ "$DATA_SOURCE" =~ ^.+:/.*$ ]]; then
    echo "NFS Data Source..."

else
	echo "DATA_SOURCE is neither NFS nor S3 pattern: $DATA_SOURCE"
fi

# mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-d1234567.efs.[region].amazonaws.com:/ /nfs

# Mount Target NFS/S3 as required
# IF NFS then mount; elif S3 then rclone

# Execute Packer
if [ "$PACK_MODE" = "PACK" ]
then
    echo "packing..."
    # time python ./packer.py --pack --source $DATA_SOURCE --tmp $STAGING_PATH --output $DATA_TARGET --key $ENCRYPTION_KEY --jobs $JOBS

elif [ "$PACK_MODE" = "UNPACK" ]
then
	echo "unpacking..."
    # time python ./packer.py --unpack --source $DATA_SOURCE --tmp $STAGING_PATH --output $DATA_TARGET --key $ENCRYPTION_KEY --jobs $JOBS
else
	echo "Unexpected PACK_MODE value: $PACK_MODE."
    exit 1
fi

echo "📦📦📦📦 Completed script: $0 📦📦📦📦"
