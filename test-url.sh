#!/bin/sh
F=/tmp/test.stat.$$
trap "rm -f $F" 0 1 2 3 14 15

sleep 1   ## Wait for any previous nc to die off..
nc -q 300 -l 8900 >$F &
NCPID=$!
trap "rm -f $F ; kill $NCPID" 0 1 2 3 14 15

./run-firefox.sh "$1" &
FFPID=$!

( sleep 30 && kill $NCPID ) >/dev/null 2>/dev/null &

wait $NCPID
kill $FFPID

head -1 $F

