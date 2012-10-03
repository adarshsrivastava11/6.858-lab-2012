#!python
import proflib, sys
selfuser = proflib.get_param('ZOOBAR_SELF')
visitor = proflib.get_param('ZOOBAR_VISITOR')

for xfer in proflib.get_xfers(selfuser):
  if xfer['sender'] == visitor:
    print 'You gave me', xfer['amount'], 'zoobars @', xfer['time']
    sys.exit(0)
  if xfer['recipient'] == visitor:
    print 'I gave you', xfer['amount'], 'zoobars @', xfer['time']
    sys.exit(0)

print 'We never exchanged zoobars!'
