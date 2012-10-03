from flask import g

import nullsandbox

def run_profile(user):
    try:
        pcode = user.profile.encode('ascii', 'ignore')
        pcode = pcode.replace('\r\n', '\n')
        return nullsandbox.run(user.username, pcode,
                               [ 'ZOOBAR_SELF=' + user.username,
                                 'ZOOBAR_VISITOR=' + g.user.person.username ])
    except Exception, e:
        return 'Exception: ' + str(e)
