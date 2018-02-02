import shlex
import subprocess


class CalledProcessError(subprocess.CalledProcessError):
    def __init__(self, returncode=0, cmd=None, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.message = ("Command '{0}' returned non-zero exit status {1}. "
                        "Output from command:\n\n{2}".
                        format(self.cmd, self.returncode, self.output))

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


def subprocess_popen(cmd):
    process = subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()  # block until return
    retcode = process.poll()
    if retcode:  # non-zero means fail
        raise CalledProcessError(retcode, cmd, stderr)
    return stdout
