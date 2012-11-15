#!/bin/sh

# Find and install PhantomJS
PHANTOMJS=phantomjs-1.7.0-linux-i686
if [ ! -d "$HOME/$PHANTOMJS" ]; then
  echo "One moment, downloading PhantomJS..."
  TEMPFILE=$(mktemp)
  TEMPDIR=$(mktemp -d)
  curl "http://phantomjs.googlecode.com/files/$PHANTOMJS.tar.bz2" > "$TEMPFILE"
  echo "Unpacking..."
  tar -C "$TEMPDIR" -xjf "$TEMPFILE"
  mv "$TEMPDIR/$PHANTOMJS" "$HOME"
  # Cleanup
  rm "$TEMPFILE"
  rmdir "$TEMPDIR"
  echo "Done"
fi
PATH=$HOME/$PHANTOMJS/bin:$PATH

SANDBOXHTML=/tmp/sb.$$.html

for P in ./profiles/good-*.html ./profiles/bad-*.html; do
  echo "------------------------------------------------"
  echo "Profile: $P"

  if ./zoobar/filter-test.py <$P >$SANDBOXHTML; then
    phantomjs test-profile.js "$SANDBOXHTML"
  else
    echo "Sandbox: rewriter error"
  fi
done

rm -f $SANDBOXHTML

