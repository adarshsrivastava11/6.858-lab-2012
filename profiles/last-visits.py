#!python
import proflib, time
selfuser = proflib.get_param('ZOOBAR_SELF')
visitor = proflib.get_param('ZOOBAR_VISITOR')

visits = []
fn = '/tmp/last_visits_%s.dat' % selfuser
try:
  with open(fn) as f:
    visits = [l.strip() for l in f.readlines()]
except IOError, e:
  if e.errno == 2:
    pass

visits = ['%s at %d' % (visitor, time.time())] + visits
visits = visits[:3]

print 'Last 3 visitors:\n', '<ul>'

for username in visits:
  print '<li>', username, '</li>'

print '</ul>'

with open(fn, 'w') as f:
  for l in visits:
    f.write(l + '\n')
