#!/bin/sh -x
if id | grep -qv uid=0; then
    echo "Must run setup as root"
    exit 1
fi

./chroot-copy.sh /bin/sh /jail
./chroot-copy.sh /usr/bin/file /jail
tar -C /jail/zoobar -jxf pypy-sandbox.tar.bz2
chown -R 0:0 /jail/zoobar/pypy-sandbox
python /jail/zoobar/pypy-sandbox/pypy/translator/sandbox/pypy_interact.py \
       /jail/zoobar/pypy-sandbox/pypy/translator/goal/pypy-c \
       >/dev/null 2>/dev/null </dev/null
mkdir -p /jail/dev
mknod --mode=666 /jail/dev/null c 1 3
mkdir -p /jail/proc
cp /proc/cpuinfo /jail/proc/cpuinfo
