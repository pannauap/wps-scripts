#!/usr/bin/env python
"""Subprocess and process management utilities.

Consolidates exec_cmd/which/program_exists/get_uid from reaver-spoof.py
and pyxiewps variants.
"""

import subprocess


def exec_cmd(cmd):
    """Run a shell command and return its stdout. Warns on non-zero exit."""
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print('Warning: command failed (rc=%d): %s' % (proc.returncode, cmd))
        if stderr:
            print('  stderr: %s' % stderr.strip())
    return stdout


def run_interactive(cmd):
    """Run a shell command, printing output in real-time, and return all stdout.

    From reaver-spoof.py's myrun().
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = []
    while True:
        line = p.stdout.readline()
        stdout.append(line)
        print line,
        if line == '' and p.poll() is not None:
            break
    return ''.join(stdout)


def which(program):
    """Check if a program exists on PATH and return its path (empty string if missing)."""
    return exec_cmd('which %s' % program).strip()


def program_exists(program):
    """Return True if the program is found on PATH."""
    return which(program) != ''


def get_uid():
    """Return the current user's UID as a string."""
    return subprocess.check_output(['id', '-u']).strip()


def get_children(pid):
    """Return list of child PIDs for a given parent PID."""
    proc = subprocess.Popen(
        'ps --no-headers -o pid --ppid %d' % pid,
        shell=True, stdout=subprocess.PIPE)
    stdout = proc.communicate()[0]
    return [int(p) for p in stdout.split()]
