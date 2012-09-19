#!/bin/sh -x
if id | grep -qv uid=0; then
    echo "Must run setup as root"
    exit 1
fi

create_socket_dir() {
    local dirname="$1"
    local ownergroup="$2"
    local perms="$3"

    mkdir -p $dirname
    chown $ownergroup $dirname
    chmod $perms $dirname
}

set_perms() {
    local ownergroup="$1"
    local perms="$2"
    local pn="$3"

    chown $ownergroup $pn
    chmod $perms $pn
}

mkdir -p /jail
cp -p index.html /jail
cp -p password.cgi /jail

./chroot-copy.sh zookd /jail
./chroot-copy.sh zookfs /jail
./chroot-copy.sh zooksvc /jail

#./chroot-copy.sh /bin/bash /jail

./chroot-copy.sh /usr/bin/env /jail
./chroot-copy.sh /usr/bin/python /jail

mkdir -p /jail/usr/lib/
cp -r /usr/lib/python2.6 /jail/usr/lib
cp -r /usr/lib/pymodules /jail/usr/lib
cp /usr/lib/libsqlite3.so.0 /jail/usr/lib

mkdir -p /jail/usr/local/lib/
cp -r /usr/local/lib/python2.6 /jail/usr/local/lib

mkdir -p /jail/etc
cp /etc/localtime /jail/etc/
cp /etc/timezone /jail/etc/

mkdir -p /jail/usr/share/zoneinfo
cp -r /usr/share/zoneinfo/America /jail/usr/share/zoneinfo/

create_socket_dir /jail/echosvc 61010:61010 755

mkdir -p /jail/tmp
chmod a+rwxt /jail/tmp

cp -r zoobar /jail/

python /jail/zoobar/zoodb.py init-person
python /jail/zoobar/zoodb.py init-transfer

