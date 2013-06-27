import subprocess
import sys


MUST_CLOSE_FDS = not sys.platform.startswith('win')

def system(command):
    # Copy/pasted from zc.buildout.
    p = subprocess.Popen(command,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=MUST_CLOSE_FDS)
    i, o, e = (p.stdin, p.stdout, p.stderr)
    i.close()
    result = o.read() + e.read()
    o.close()
    e.close()
    output = result.decode()
    exit_code = p.wait()
    return exit_code, output
