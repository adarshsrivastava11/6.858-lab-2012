from flask import g, render_template, request, Markup

from login import requirelogin
from zoodb import *
from debug import *
from profile import *

@catch_err
@requirelogin
def users():
    args = {}
    args['req_user'] = Markup(request.args.get('user', ''))
    if 'user' in request.values:
        user = g.persondb.query(Person).get(request.values['user'])
        if user:
            if user.profile.startswith("#!python"):
                p = run_profile(user)
            else:
                p = user.profile
            args['profile'] = Markup("<b>%s</b>" % p)
            args['user'] = user
            args['transfers'] = g.transferdb.query(Transfer).filter(
                                    or_(Transfer.sender==user.username,
                                        Transfer.recipient==user.username))
        else:
            args['warning'] = "Cannot find that user."
    return render_template('users.html', **args)
