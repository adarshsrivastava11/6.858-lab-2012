import sys, time

## We have to do this here, because 'import site' (i.e., omitting -S)
## can sometimes fail, because getpwnam() might fail, and we want to
## avoid requiring a fully-populated passwd file in the chroot jail.
sys.path += ['/usr/lib/pymodules/python2.6']

import zoodb
import sqlalchemy

def parse_kv(argv):
    kv = {}
    for arg in argv:
        pos = arg.find('=')
        if pos < 0:
            continue
        k = arg[:pos]
        v = arg[pos+1:]
        kv[k] = v
    return kv

def get_param(key):
    kv = parse_kv(sys.argv)
    return kv.get(key)

def get_xfers(username):
    xfer_db = zoodb.transfer_setup()
    xfers = []
    for xfer in xfer_db.query(zoodb.Transfer).filter(
                    sqlalchemy.or_(zoodb.Transfer.sender==username,
                                   zoodb.Transfer.recipient==username)):
        xfers += [{'sender': xfer.sender,
                   'recipient': xfer.recipient,
                   'amount': xfer.amount,
                   'time': xfer.time}]
    return xfers

def get_user(username):
    person_db = zoodb.person_setup()
    p = person_db.query(zoodb.Person).get(username)
    if not p:
        return None
    return {'username': p.username,
            'profile': p.profile,
            'zoobars': p.zoobars}

def xfer(rcptname, zoobars):
    selfname = get_param('ZOOBAR_SELF')

    person_db = zoodb.person_setup()
    xfer_db = zoodb.transfer_setup()

    sender = person_db.query(zoodb.Person).get(selfname)
    recipient = person_db.query(zoodb.Person).get(rcptname)

    if not sender:
        raise Exception('sender ' + selfname + ' not found')
    if not recipient:
        raise Exception('recipient ' + rcptname + ' not found')

    sender_balance = sender.zoobars - zoobars
    recipient_balance = recipient.zoobars + zoobars

    if sender_balance < 0 or recipient_balance < 0:
        raise ValueError()

    sender.zoobars = sender_balance
    recipient.zoobars = recipient_balance
    
    transfer = zoodb.Transfer()
    transfer.sender = sender.username
    transfer.recipient = recipient.username
    transfer.amount = zoobars
    transfer.time = time.asctime()
    xfer_db.add(transfer)

    person_db.commit()
    xfer_db.commit()

