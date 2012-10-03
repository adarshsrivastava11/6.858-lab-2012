import os, sys, errno
from cStringIO import StringIO

pypy_sandbox_dir = '/zoobar/pypy-sandbox'
sys.path = [pypy_sandbox_dir] + sys.path

from pypy.translator.sandbox import pypy_interact, sandlib, vfs
from pypy.translator.sandbox.vfs import Dir, RealDir, RealFile
from pypy.rpython.module.ll_os_stat import s_StatResult
from pypy.tool.lib_pypy import LIB_ROOT

class WritableFile(vfs.RealFile):
    def __init__(self, basenode):
        self.path = basenode.path
    def open(self):
        try:
            return open(self.path, 'wb')
        except IOError, e:
            raise OSError(e.errno, 'write open failed')

class MySandboxedProc(pypy_interact.PyPySandboxedProc):
    def __init__(self, profile_owner, code, args):
        super(MySandboxedProc, self).__init__(
            pypy_sandbox_dir + '/pypy/translator/goal/pypy-c',
            ['-S', '-c', code] + args
        )
        self.debug = False
        self.virtual_cwd = '/'

    ## Replacements for superclass functions
    def get_node(self, vpath):
        dirnode, name = self.translate_path(vpath)
        if name:
            node = dirnode.join(name)
        else:
            node = dirnode
        if self.debug:
            sandlib.log.vpath('%r => %r' % (vpath, node))
        return node

    def handle_message(self, fnname, *args):
        if '__' in fnname:
            raise ValueError("unsafe fnname")
        try:
            handler = getattr(self, 'do_' + fnname.replace('.', '__'))
        except AttributeError:
            raise RuntimeError("no handler for " + fnname)
        resulttype = getattr(handler, 'resulttype', None)
        return handler(*args), resulttype

    def build_virtual_root(self):
        # build a virtual file system:
        # * can access its own executable
        # * can access the pure Python libraries
        # * can access the temporary usession directory as /tmp
        exclude = ['.pyc', '.pyo']
        tmpdirnode = RealDir('/tmp/sandbox-root', exclude=exclude)
        libroot = str(LIB_ROOT)

        return Dir({
            'bin':  Dir({'pypy-c':     RealFile(self.executable),
                         'lib-python': RealDir(libroot + '/lib-python', exclude=exclude),
                         'lib_pypy':   RealDir(libroot + '/lib_pypy',   exclude=exclude)
                        }),
            'proc': Dir({'cpuinfo': RealFile('/proc/cpuinfo'), }),
            'tmp':  tmpdirnode,
            })

    ## Implement / override system calls
    ##
    ## Useful reference:
    ##    pypy-sandbox/pypy/translator/sandbox/sandlib.py
    ##    pypy-sandbox/pypy/translator/sandbox/vfs.py
    ##
    def do_ll_os__ll_os_geteuid(self):
        return 0

    def do_ll_os__ll_os_getuid(self):
        return 0

    def do_ll_os__ll_os_getegid(self):
        return 0

    def do_ll_os__ll_os_getgid(self):
        return 0

    def do_ll_os__ll_os_fstat(self, fd):
        ## Limitation: fd's 0, 1, and 2 are not in open_fds table
        f = self.get_file(fd)
        try:
            return os.fstat(f.fileno())
        except:
            raise OSError(errno.EINVAL)
    do_ll_os__ll_os_fstat.resulttype = s_StatResult

    def do_ll_os__ll_os_open(self, vpathname, flags, mode):
        if flags & (os.O_CREAT):
            dirnode, name = self.translate_path(vpathname)
            ## LAB 3: handle file creation

        node = self.get_node(vpathname)
        if flags & (os.O_RDONLY|os.O_WRONLY|os.O_RDWR) != os.O_RDONLY:
            ## LAB 3: handle writable files, by not raising OSError in some cases
            raise OSError(errno.EPERM, "write access denied")
            node = WritableFile(node)

        f = node.open()
        return self.allocate_fd(f)

    def do_ll_os__ll_os_write(self, fd, data):
        try:
            f = self.get_file(fd)
        except:
            f = None

        if f is not None:
            ## LAB 3: if this file should be writable, do the write,
            ##        and return the number of bytes written
            raise OSError(errno.EPERM, "write not implemented yet")

        return super(MySandboxedProc, self).do_ll_os__ll_os_write(fd, data)

def run(profile_owner, code, args = [], timeout = None):
    sandproc = MySandboxedProc(profile_owner, code, args)

    if timeout is not None:
        sandproc.settimeout(timeout, interrupt_main=True)
    try:
        code_output = StringIO()
        sandproc.interact(stdout=code_output, stderr=code_output)
        return code_output.getvalue()
    finally:
        sandproc.kill()

