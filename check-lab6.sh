#!/bin/sh
SANDBOXHTML=/tmp/sb.$$.html

httpreq() {
  if echo "$1" | grep -q GET./test-ok; then
    echo "OK"
  elif echo "$1" | grep -q GET./test-bad; then
    echo "Escaped"
  elif echo "$1" | grep -q GET./test-broken; then
    DETAIL=$(echo "$1" | grep -o '/test-broken-[0-9]\+')
    echo "Broken: $DETAIL"
  else
    echo "Unknown"
  fi
}

for P in ./profiles/good-*.html ./profiles/bad-*.html; do
  echo "------------------------------------------------"
  echo "Profile: $P"
  # TRAW=$(httpreq "$(./test-url.sh $P 2>/dev/null)")
  # echo "Raw:     $TRAW"

  if ./zoobar/filter-test.py <$P >$SANDBOXHTML; then
    TSANDBOX=$(httpreq "$(./test-url.sh $SANDBOXHTML 2>/dev/null)")
    echo "Sandbox: $TSANDBOX"
  else
    echo "Sandbox: rewriter error"
  fi
done

rm -f $SANDBOXHTML

