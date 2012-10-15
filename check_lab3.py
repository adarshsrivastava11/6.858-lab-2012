#!/usr/bin/python

import datetime
import os
import sys
import atexit
import time
import subprocess
import traceback
import re
import urllib
import base64

import z_client as z

thisdir = os.path.dirname(os.path.abspath(__file__))
verbose = False

def green(s):
    return '\033[1;32m%s\033[m' % s

def red(s):
    return '\033[1;31m%s\033[m' % s

def log(*m):
    print >> sys.stderr, " ".join(m)

def log_exit(*m):
    log(red("ERROR:"), *m)
    exit(1)

def file_read(pn, size=-1):
    with open(pn) as fp:
        return fp.read(size)

def log_to_file(*m):
    with open('/tmp/html.out', 'a') as fp:
        print >> fp, " ".join(m)

def sh(cmd, exit_onerr=True):
    if verbose: log("+", cmd)
    if os.system(cmd) != 0 and exit_onerr:
        log_exit("running shell command:", cmd)

pwfiles = ['passwd', 'passwd-', 'shadow', 'shadow-', 'group', 'group-']
def clean_env():
    # remove /jail and reset password/group files
    if os.path.exists("/jail"):
        sh("mv /jail /jail.bak")

    for f in pwfiles:
        if not os.path.exists(os.path.join(thisdir, "env", f)):
            log_exit("missing '%s' file in test dir" % f)

    for f in pwfiles:
        sh("mv /etc/%s /etc/%s.bak" % (f, f))
        sh("cp %s/env/%s /etc/%s" % (thisdir, f, f))

    atexit.register(restore_env)

def restore_env():
    for f in pwfiles:
        sh("mv /etc/%s.bak /etc/%s" % (f, f))

    log("+ restoring /jail; test /jail saved to /jail.check..")
    if os.path.exists("/jail.check"):
        sh("rm -rf /jail.check")
    sh("mv /jail /jail.check")
    if os.path.exists("/jail.bak"):
        sh("mv /jail.bak /jail")

def check_root():
    if os.geteuid() != 0:
        log_exit("must run %s as root" % sys.argv[0])

def killall():
    sh("killall zookld zookd zookfs zooksvc >/dev/null 2>&1", exit_onerr=False)

def setup():
    log("+ setting up environment in fresh /jail..")
    check_root()
    killall()
    clean_env()

    log("+ running make.. output in /tmp/make.out")
    sh("make clean >/dev/null")
    sh("make all setup >/tmp/make.out 2>&1")
    sh("rm -f /tmp/html.out")

    log("+ running zookld in the background.. output in /tmp/zookld.out")
    zookld_out = open("/tmp/zookld.out", "w")
    subprocess.Popen(["./zookld"], stdout=zookld_out, stderr=zookld_out)

    log("+ profile output logged in /tmp/html.out")

    atexit.register(killall)

    time.sleep(5)

def check_ex0():
    x = z.check()
    if not x[0]:
        log(red("FAIL"), "Exercise 1: App functionality", x[1])
        exit(1)
    else:
        log(green("PASS"), "Exercise 1: App functionality")

def update_profile(cookie, code):
    z.post("http://localhost:8080/zoobar/index.cgi", cookie,
           "profile_update=%s&profile_submit=Save" % urllib.quote_plus(code))

def check_profile_internal(logmsg, code, prof_pat,
                           user1="test1", pass1="pass",
                           user2="test2", pass2="pass"):
    ## login as user test1
    html1, cookies1 = z.login(user1, pass1)

    ## update test1 profile
    update_profile(cookies1, code)

    ## login as user test2
    html2, cookies2 = z.login(user2, pass2)

    ## fetch test1 profile
    vhtml = z.view_user(cookies2, user1)

    ## log profile output 
    log_to_file("=" * 60)
    log_to_file(logmsg)
    log_to_file("")
    log_to_file(vhtml)
    log_to_file("")

    ## check for profile pattern
    return "Traceback" not in vhtml and re.search(prof_pat, vhtml, re.DOTALL) is not None

## profile generation patterns
wrapper_pat = '''
try:
    if check():
        print "SUCCESS"
    else:
        print "ERROR : check failed"
except BaseException, e:
    import traceback
    print "ERROR : caught exception"
    print traceback.format_exc()
'''

file_read_pat = '''#!python
def check():
    import os, base64
    print "Opening file %(path)s"
    fd = os.open("%(path)s", os.O_RDONLY)
    print "Opened file %(path)s"
    d  = os.read(fd, %(length)d)
    os.close(fd)
    print "Read '" + d + "' from file"
    return base64.b64encode(d) == "%(data)s"
'''

file_write_pat = '''#!python
def check():
    import os
    print "Opening file %(path)s"
    fd = os.open("%(path)s", os.O_CREAT | os.O_RDWR)
    print "Opened file %(path)s"
    d  = "%(data)s"
    l  = os.write(fd, d)
    os.close(fd)
    print "Wrote " + str(l) + " bytes"
    return l == len(d)
'''

def file_read_check(logmsg, sbpath, realpath=None, data=None,
                    user1="test1", pass1="pass",
                    user2="test2", pass2="pass"):
    if not data:
        data = file_read(realpath, 10)
        
    code = file_read_pat % {'path': sbpath, 'data': base64.b64encode(data), 'length': len(data)}
    code += wrapper_pat
    return check_profile_internal(logmsg, code, "SUCCESS", user1, pass1, user2, pass2)

def file_write_check(logmsg, sbpath, data=None,
                    user1="test1", pass1="pass",
                    user2="test2", pass2="pass"):
    if not data:
        data = "file_write_check test string"
        
    code = file_write_pat % {'path': sbpath, 'data': data}
    code += wrapper_pat
    if not check_profile_internal(logmsg, code, "SUCCESS", user1, pass1, user2, pass2):
        return False
    
    return file_read_check(logmsg + "read and compare:", sbpath, None, data, user1, pass1, user2, pass2)

def check_profile(prof_py, prof_pat, msg):
    code = file_read(os.path.join(thisdir, "profiles", prof_py))
    ret = check_profile_internal("%s:" % msg, code, prof_pat)
    if not ret:
        log(red("FAIL"), "Profile", prof_py, ":", msg)
    return ret

def check_sandbox():
    if file_read_check("Exercise 2: Sandbox:", "/zoobar/media/zoobar.css",
                       "/jail/zoobar/media/zoobar.css"):
        log(red("FAIL"), "Exercise 2: Sandbox check")
        return False
    else:
        log(green("PASS"), "Exercise 2: Sandbox check")
        return True

def check_hello():
    pat = "profile.*Hello,.*test2.*Current time: \d+\.\d+"
    if check_profile("hello-user.py", pat, "Hello user check"):
        log(green("PASS"), "Profile hello-user.py")

def check_visit_tracker_1():
    pat = "profile.*Hello,.*test2.*Your visit count: 0.*Your last visit: never"
    return check_profile("visit-tracker.py", pat, "First visit check")

def check_visit_tracker_2():
    pat = "profile.*Hello,.*test2.*Your visit count: 1.*Your last visit: \d+\.\d+"
    return check_profile("visit-tracker.py", pat, "Second visit check")

def check_visit_tracker():
    if check_visit_tracker_1() and check_visit_tracker_2():
        log(green("PASS"), "Profile visit-tracker.py")

def check_last_visits_1():
    pat = "profile.*Last 3 visitors:.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (1/3)")

def check_last_visits_2():
    pat = "profile.*Last 3 visitors:.*test2 at \d+.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (2/3)")

def check_last_visits_3():
    pat = "profile.*Last 3 visitors:.*test2 at \d+.*test2 at \d+.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (3/3)")

def check_last_visits():
    if check_last_visits_1() and check_last_visits_2() and check_last_visits_3():
        log(green("PASS"), "Profile last-visits.py")

def check_xfer_tracker_1():
    now = datetime.datetime.now()
    pat = "profile.*I gave you 3 zoobars \@ .* %d" % now.year
    return check_profile("xfer-tracker.py", pat, "Transfer tracker check")

# def check_xfer_tracker_2():
#     html2, cookies2 = z.login("test2", "pass")
#     thtml = z.transfer(cookies2, "test1", 3)
#     pat = "profile.*You gave me 3 zoobars \@"
#     return check_profile("xfer-tracker.py", pat)

def check_xfer_tracker():
    if check_xfer_tracker_1():
        log(green("PASS"), "Profile xfer-tracker.py")

def check_granter_1():
    pat = "profile.*Thanks for visiting.  I gave you one zoobar."
    if not check_profile("granter.py", pat, "Zoobar grant check"):
        return False

    # check that profile owner token was used and not visitor's, by checking 
    # that profile owner has one less zoobar
    html, cookies = z.login("test1", "pass")
    if not z.check_zoobars(html, "test1", 6, "")[0]:
        log(red("FAIL"), "Exercises 1-5:", "Not using profile owner's token")

    return True

def check_granter_2():
    pat = "profile.*I gave you a zoobar .* seconds ago"
    return check_profile("granter.py", pat, "'Greedy visitor check1")

def check_granter_3():
    html3, cookies3 = z.register("test3", "pass")
    z.transfer(cookies3, "test2", 10)
    pat = "profile.*You have \d+ already; no need for more"
    return check_profile("granter.py", pat, "Greedy visitor check2")

def check_granter_4():
    html1, cookies1 = z.login("test1", "pass")
    z.transfer(cookies1, "test2", 6)
    pat = "profile.*Sorry, I have no more zoobars"
    return check_profile("granter.py", pat, "'I am broke' check")

def check_granter():
    if check_granter_1() and check_granter_2() and \
        check_granter_3() and check_granter_4():
        log(green("PASS"), "Profile granter.py")

# check that /tmp is separate for different users
def check_tmp():
    tmpfile = "/tmp/testfile"
    data    = "tmp check test string"

    # write to /tmp as user test1
    if not file_write_check("Exercise 3: /tmp write:", tmpfile, data,
                            "test1", "pass", "test2", "pass"):
        log(red("FAIL"), "Exercise 3: /tmp check (could not write to /tmp)")
        return

    # try to read the same file
    if file_read_check("Exercise 3: shared /tmp:", tmpfile, None, data,
                       "test2", "pass", "test1", "pass"):
        log(red("FAIL"), "Exercise 3: /tmp check (/tmp shared by more than one user)")
        return

    # try to read the same file, sneaky edition
    z.register("test1/.", "pass")
    if file_read_check("Exercise 3: shared /tmp:", tmpfile, None, data,
                       "test1/.", "pass", "test1", "pass"):
        log(red("FAIL"), "Exercise 3: /tmp check (special characters in usernames)")
        return

    log(green("PASS"), "Exercise 3: /tmp check")

def check_nontmp_write_internal(nontmp_file):
    if file_write_check("Exercise 3: non-tmp write:", nontmp_file):
        log(red("FAIL"), "Exercise 3: Can write to non /tmp files")
        return False

    if file_write_check("Exercise 3: non-tmp write via ..:",
                        "/tmp/..%s" % nontmp_file):
        log(red("FAIL"), "Exercise 3: Can write to non /tmp files via ..")
        return False

    if file_write_check("Exercise 3: non-tmp write via ../..:",
                        "/tmp/../..%s" % nontmp_file):
        log(red("FAIL"), "Exercise 3: Can write to non /tmp files via ../..")
        return False

    return True

def check_nontmp_write():
    return check_nontmp_write_internal("/bin/lib-python/testfile") and \
        check_nontmp_write_internal("/testfile")
    
dir_pat = '''#!python
def check():
    import os
    print "os.%(func)s : %(dir)s"
    os.%(func)s("%(dir)s")
    print "os.%(func)s : %(dir)s : successful"
    return True
'''

def dir_prof(func, dir):
    code = dir_pat % {'func': func, 'dir': dir}
    return code + wrapper_pat
    
def check_dir_funcs():
    tmpdir = "/tmp/testdir"

    if not check_profile_internal("Challenge 1: mkdir:",
                                  dir_prof('mkdir', tmpdir), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Cannot create /tmp dirs")
        return False

    if not check_profile_internal("Challenge 1: rmdir:",
                                  dir_prof('rmdir', tmpdir), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Cannot rmdir /tmp dirs")
        return False

    check_profile_internal("Challenge 1: mkdir2:", dir_prof('mkdir', tmpdir), "SUCCESS")
    if not file_write_check("Challenge 1: mkdir file-write:", "%s/testfile" % tmpdir):
        log(red("FAIL"), "Challenge 1: Cannot write to created /tmp dirs")
        return False

    nontmpdir = "/testdir"
    if check_profile_internal("Challenge 1: non-tmp mkdir:",
                              dir_prof('mkdir', nontmpdir), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can create non /tmp dirs")
        return False

    if check_profile_internal("Challenge 1: non-tmp mkdir via ..:",
                              dir_prof('mkdir', "/tmp/..%s" % nontmpdir), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can create non /tmp dirs via ..")
        return False

    if check_profile_internal("Challenge 1: non-tmp mkdir via ../..:",
                              dir_prof('mkdir', "/tmp/../..%s" % nontmpdir), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can create non /tmp dirs via ../..")
        return False

    return True

rename_pat = '''#!python
def check():
    import os
    print "Renaming file from %(from)s to %(to)s"
    os.rename("%(from)s", "%(to)s")
    print "Renamed file from %(from)s to %(to)s"
    return True
'''

def check_rename():
    fn   = "/tmp/rename_test"
    data = "rename check test string"
    if not file_write_check("Challenge 1: rename: file write:", fn, data):
        log(red("FAIL"), "Challenge 1: Cannot create file %s for rename test" % fn)
        return False

    code = rename_pat % {'from': fn, 'to': fn + '.bak'}
    code += wrapper_pat
    if not check_profile_internal("Challenge 1: rename: file rename:", code, "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Cannot rename file %s in /tmp" % fn)
        return False

    if not file_read_check("Challenge 1: rename: file read:", fn + ".bak", None, data):
        log(red("FAIL"), "Challenge 1: Read failed for renamed file %s in /tmp" % fn)
        return False        

    return True

unlink_pat = '''#!python
def check():
    import os
    print "Unlinking file %(path)s"
    os.unlink("%(path)s")
    print "Unlinked file %(path)s"
    return True
'''

def check_unlink():
    def unlink_prof(filename):
        code = unlink_pat % {'path': filename}
        return code + wrapper_pat

    fn = "/tmp/unlink_test"
    if not file_write_check("Challenge 1: unlink: file write:", fn):
        log(red("FAIL"), "Challenge 1: Cannot create file %s for unlink test" % fn)
        return False

    if not check_profile_internal("Challenge 1: unlink: file unlink:", unlink_prof(fn), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Cannot unlink file %s in /tmp" % fn)
        return False

    nontmpfile = "/bin/lib-python/stdlib-version.txt"
    if check_profile_internal("Challenge 1: non-tmp unlink:", unlink_prof(nontmpfile), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can unlink file %s not in /tmp" % nontmpfile)
        return False

    if check_profile_internal("Challenge 1: non-tmp unlink via ..:",
                              unlink_prof("/tmp/..%s" % nontmpfile), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can unlink file %s not in /tmp via .." % nontmpfile)
        return False

    if check_profile_internal("Challenge 1: non-tmp unlink via ../..:",
                              unlink_prof("/tmp/../..%s" % nontmpfile), "SUCCESS"):
        log(red("FAIL"), "Challenge 1: Can unlink file %s not in /tmp via ../.." % nontmpfile)
        return False

    return True

def check_challenge1():
    ret = check_dir_funcs()
    ret = check_rename() and ret
    ret = check_unlink() and ret

    if ret:
        log(green("PASS"), "Challenge 1")

symlink_pat = '''#!python
def check():
    import os, base64
    print "Symlinking %(dst)s to %(src)s"
    os.symlink("%(src)s", "%(dst)s")
    print "Symlinked %(dst)s to %(src)s. Reading %(dst)s"

    fd = os.open("%(dst)s", os.O_RDONLY)
    print "Opened %(dst)s. Reading it.."
    d  = os.read(fd, %(length)d)
    print "Read %(dst)s. Checking contents.."
    return base64.b64encode(d) == "%(data)s"
'''

def check_challenge2():
    
    def symlink_check(logmsg, src, dst, data):
        code = symlink_pat % {'src': src, 'dst': dst, 'length': len(data),
                              'data': base64.b64encode(data)}
        code += wrapper_pat
        return check_profile_internal(logmsg, code, "SUCCESS")

    fn = "/tmp/symlink_target"
    d  = "symlink check test string"
    if not file_write_check("Challenge 2: symlink: file write:", fn, d):
        log(red("FAIL"), "Challenge 2: Cannot create file %s for symlink test" % fn)
        return False

    if not symlink_check("Challenge 2: symlink:", fn, "/tmp/sym", d):
        log(red("FAIL"), "Challenge 2: Cannot create symlinks in /tmp")
        return

    nontmpfile = "/zoobar/media/zoobar.css"
    d = file_read("/jail/%s" % nontmpfile, 32)
    result = True

    if symlink_check("Challenge 2: symlink to non-tmp file:", nontmpfile, "/tmp/sym2", d):
        log(red("FAIL"), "Challenge 2: Can create symlinks to non /tmp files")
        result = False

    if symlink_check("Challenge 2: symlink to non-tmp file via .. (1/2):",
                     "/tmp/..%s" % nontmpfile, "/tmp/sym3", d):
        log(red("FAIL"), "Challenge 2: Can create symlinks to non /tmp files via .. (1/2)")
        result = False

    if symlink_check("Challenge 2: symlink to non-tmp file via .. (2/2):",
                     "..%s" % nontmpfile, "/tmp/sym3", d):
        log(red("FAIL"), "Challenge 2: Can create symlinks to non /tmp files via .. (2/2)")
        result = False

    if symlink_check("Challenge 2: symlink to non-tmp file via ../.. (1/2):",
                     "/tmp/../..%s" % nontmpfile, "/tmp/sym3", d):
        log(red("FAIL"), "Challenge 2: Can create symlinks to non /tmp files via ../.. (1/2)")
        result = False

    if symlink_check("Challenge 2: symlink to non-tmp file via ../.. (2/2):",
                     "../..%s" % nontmpfile, "/tmp/sym3", d):
        log(red("FAIL"), "Challenge 2: Can create symlinks to non /tmp files via ../.. (2/2)")
        result = False

    if result:
        log(green("PASS"), "Challenge 2")

def main():
    if '-v' in sys.argv:
        global verbose
        verbose = True

    try:
        setup()
        check_ex0()

        check_hello()
        check_visit_tracker()
        check_last_visits()
        check_xfer_tracker()
        check_granter()

        if check_sandbox():
            check_tmp()
            check_nontmp_write()

            check_challenge1()
            check_challenge2()
    except Exception:
        log_exit(traceback.format_exc())

if __name__ == "__main__":
    main()
