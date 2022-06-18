#! /bin/bash
set -e

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
# IF NFS then mount; elif S3 then rclone;
#   NFS pattern: "fs-d1234567.efs.[region].amazonaws.com:/sub0/sub1/"
#   S3 pattern:  "S3://bucket-name/key-name"

mkdir -p $STAGING_PATH

# Parse the source string
if [[ "$DATA_SOURCE" =~ ^[S|s]3://.+/.* ]]; then
	echo "S3 Data source..."
    S3_SOURCE_BUCKET=`echo $DATA_SOURCE | sed -E 's/([^:]+).(.*)/\1/'`
    S3_SOURCE_KEY=`echo $DATA_SOURCE | sed -E 's/([^:]+).(.*)/\2/'`
    echo "[TODO] S3 bucket: $S3_SOURCE_BUCKET , S3 path: $S3_SOURCE_KEY ..."
    echo "[TODO] rclone from S3 bucket: $S3_SOURCE_BUCKET , S3 path: $S3_SOURCE_KEY ..."
    # TODO rclone to local /s3
elif [[ "$DATA_SOURCE" =~ ^.+:/.*$ ]]; then
    echo "NFS Data Source..."
    NFS_SOURCE_HOST=`echo $DATA_SOURCE | sed -E 's/([^:]+).(.*)/\1/'`
    NFS_SOURCE_PATH=`echo $DATA_SOURCE | sed -E 's/([^:]+).(.*)/\2/'`
    echo "[TODO] Mounting Source NFS endpoint: $NFS_SOURCE_HOST ..."
    # TODO mount at /nfs , nice to have: check if already mounted.
    mkdir /nfs
    mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $NFS_SOURCE_HOST:/ /nfs
    echo "NFS_SOURCE_PATH: $NFS_SOURCE_PATH"
    MOUNTED_DATA_SOURCE="/nfs$NFS_SOURCE_PATH"
    echo "MOUNTED_DATA_SOURCE: $MOUNTED_DATA_SOURCE: , size of path: "`du -sh $MOUNTED_DATA_SOURCE`
else
	echo "DATA_SOURCE is neither NFS nor S3 pattern: $DATA_SOURCE"
fi

# Parse the target string
if [[ "$DATA_TARGET" =~ ^[S|s]3://.+/.* ]]; then
	echo "S3 Data Target..."
    S3_TARGET_BUCKET=`echo $DATA_TARGET | sed -E 's/([^:]+).(.*)/\1/'`
    S3_TARGET_KEY=`echo $DATA_TARGET | sed -E 's/([^:]+).(.*)/\2/'`
    echo "[TODO] S3 bucket: $S3_TARGET_BUCKET , S3 path: $S3_TARGET_KEY ..."
    echo "[TODO] rclone from S3 bucket: $S3_TARGET_BUCKET , S3 path: $S3_TARGET_KEY ..."
    # TODO rclone to local /s3
elif [[ "$DATA_TARGET" =~ ^.+:/.*$ ]]; then
    echo "NFS Data Target..."
    NFS_TARGET_HOST=`echo $DATA_TARGET | sed -E 's/([^:]+).(.*)/\1/'`
    NFS_TARGET_PATH=`echo $DATA_TARGET | sed -E 's/([^:]+).(.*)/\2/'`
    echo "[TODO] Mounting Target NFS endpoint: $NFS_TARGET_HOST ..."
    # TODO mount at /nfs , nice to have: check if already mounted, and NFS_SOURCE_HOST == NFS_TARGET_HOST
    # mkdir /nfs_target
    # mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $NFS_SOURCE_HOST /nfs
    echo "NFS_TARGET_PATH: $NFS_TARGET_PATH"
    MOUNTED_DATA_TARGET="/nfs$NFS_TARGET_PATH"
    echo "[DEBUG] MOUNTED_DATA_TARGET: $MOUNTED_DATA_TARGET: , size of path: "`du -sh $MOUNTED_DATA_TARGET`
else
	echo "DATA_TARGET is neither NFS nor S3 pattern: $DATA_TARGET"
    echo "Using local EBS storage as DATA_TARGET: $DATA_TARGET"
    mkdir -p $DATA_TARGET
fi

# Retrieve encryption key.
aws secretsmanager get-secret-value --secret-id $ENCRYPTION_KEY | jq -r '.SecretString' > $ENCRYPTION_KEY

# Execute Packer
if [ "$PACK_MODE" = "PACK" ]
then
    echo "📦📦📦📦  Packing..."
    time python ./packer.py --pack --source $MOUNTED_DATA_SOURCE --tmp $STAGING_PATH --output $DATA_TARGET --key $ENCRYPTION_KEY --jobs $JOBS

    echo "📦📦📦📦  Setting up Nginx..."
    apt install -y nginx
    ufw allow 'Nginx HTTP'
    cp -f /etc/nginx/sites-available/default /etc/nginx/sites-available-default-orig.bak
    cp -f /root/packer/aws/etc-nginx-sites-available-default /etc/nginx/sites-available/default
    systemctl restart nginx
    systemctl status nginx
    curl localhost


elif [ "$PACK_MODE" = "UNPACK" ]
then
	echo "📦📦📦📦  Unpacking..."
    time python ./packer.py --unpack --source $MOUNTED_DATA_SOURCE --tmp $STAGING_PATH --output $DATA_TARGET --key $ENCRYPTION_KEY --jobs $JOBS
else
	echo "Unexpected PACK_MODE value: $PACK_MODE."
    exit 1
fi

echo "📦📦📦📦 Completed script: $0 📦📦📦📦"
