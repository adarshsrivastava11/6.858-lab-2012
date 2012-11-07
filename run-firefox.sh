#!/bin/sh
D=/tmp/firefox-home.$$
mkdir -p $D

Xvfb :99 &
XPID=$!

trap "rm -rf $D ; /bin/kill $XPID" 0 1 2 3 14 15
DISPLAY=:99 HOME=$D exec firefox "$@"
