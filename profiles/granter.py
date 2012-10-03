#!python
import proflib, sys, time
selfuser = proflib.get_param('ZOOBAR_SELF')
visitor = proflib.get_param('ZOOBAR_VISITOR')

me = proflib.get_user(selfuser)
if me['zoobars'] <= 0:
  print 'Sorry, I have no more zoobars'
  sys.exit(0)

you = proflib.get_user(visitor)
if you['zoobars'] > 20:
  print 'You have', you['zoobars'], 'already; no need for more'
  sys.exit(0)

last_fn = '/tmp/last_freebie_%s_%s.dat' % (selfuser, visitor)
last_xfer = 0
try:
  with open(last_fn) as f:
    last_xfer = float(f.read())
except IOError, e:
  if e.errno == 2:
    pass

now = time.time()
if now - last_xfer < 60:
  print 'I gave you a zoobar %.1f seconds ago' % (now-last_xfer)
  sys.exit(0)

proflib.xfer(visitor, 1)
print 'Thanks for visiting.  I gave you one zoobar.'

with open(last_fn, 'w') as f:
  f.write(str(now))

