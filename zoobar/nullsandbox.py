import signal, subprocess

def run(profile_owner, code, args):
    h = signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    try:
        return subprocess.Popen(['env', '-', 'PYTHONPATH=/zoobar',
                                 'python', '-S', '-c', code] + args,
                                stdout=subprocess.PIPE).communicate()[0]
    finally:
        signal.signal(signal.SIGCHLD, h)

