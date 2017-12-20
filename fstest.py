import pytest
import subprocess
import sys
import os
from StringIO import StringIO
from subprocess import PIPE

ROOTDIR = '/testfs'
FNULL = open(os.devnull, 'w')
filesystems = ('xfs', 'ntfs', 'exfat')
subdirs = ('dir', 'subdir')

setdircommand = 'sudo pdp-flbl {0}:0:0xffffffffffffff:ccnr {1}'
setfcommand = 'sudo pdp-flbl {0} {1}'
getdircommand = 'sudo pdp-ls -lMnd {0}'
getfcommand = 'sudo pdp-ls -lMn {0}'

def stRes(res):
    return '...SUCSESS' if res == 0 else "...FAIL"


def printResult(indent, command, res, sout, serr, supress):
    msg =  '{0}{1}...{2}'.format(indent, command, stRes(res))
    if not supress:
        msg += '\n{0}{0}output: {1}'.format(indent, sout.strip())
    if res:
        msg += '\n{0}({1})'.format(indent, serr.strip())
    print(msg)


def printGetResult(indent, command, res, sout, serr):
    msg = '{0}get: {1}....{2}'.format(
        indent,
        command.split()[-1],
        ''.join(sout.split()[4:5]))
    print(msg)

def printSetResult(indent, command, res, sout, serr):
    msg = '{0}set: {1} to {2}....{3}'.format(
        indent,
        command.split()[-1],
        command.split()[-2],
        stRes(res))
    if res:
        msg += '\n{0}{0}{1}'.format(indent, serr.strip())
    print(msg)

def runCommand(command, indent='', supress=True, isset=False, isget=False):
    scommand = command.split()
    pipe = subprocess.Popen(scommand, stdout=PIPE, stderr=PIPE)
    sout, serr = pipe.communicate()
    res = pipe.returncode
    if isget:
        printGetResult(indent, command, res, sout, serr)
    elif isset:
        printSetResult(indent, command, res, sout, serr)
    else:
        printResult(indent, command, res, sout, serr, supress)


def setup_module(module):
    print("\n...basic setup into this module")

    command = 'sudo mkdir {0}'.format(ROOTDIR)
    runCommand(command)

    command = 'sudo chown user:disk {0}'.format(ROOTDIR)
    runCommand(command)
    print 80*'*'

    for i, fs in enumerate(filesystems):
        dirname = os.path.join(ROOTDIR, fs)

        command = 'sudo mkdir -p {0}'.format(dirname)
        runCommand(command)

        command = 'sudo mkfs.{0} /dev/ram{1}'.format(fs, i)
        runCommand(command)

        command = 'sudo mount /dev/ram{0} {1}'.format(i, dirname)
        runCommand(command)

        subdirname = dirname
        for subdir in subdirs:
            subdirname = os.path.join(subdirname, subdir)

        command = 'sudo mkdir -p {0}'.format(subdirname)
        runCommand(command)

        command = 'sudo chown -R user:disk {0}'.format(dirname)
        runCommand(command)

        with open(os.path.join(subdirname, 'testfile.txt'), 'w') as f:
            f.write('This is a test file...\n')
            print('fill file {0}...done'.format(f.name))
        print 80*'*'

    command = 'sudo pdp-flbl -f 3:0:0xffffffffffffff:ccnr {0}'.format(ROOTDIR)
    runCommand(command)
    print('...setup done')


def teardown_module(module):
    print
    for i, fs in enumerate(filesystems):
        dirname = os.path.join(ROOTDIR, fs)
        command = 'sudo fusermount -u {0}'.format(dirname)
        runCommand(command)

        command = 'sudo blockdev --flushbufs /dev/ram{0}'.format(i)
        runCommand(command)

    command = 'sudo rm -rf {0}'.format(ROOTDIR)
    runCommand(command)


def test_init():
    print 80*'*'
    assert True


def rectest(dirname, r=4, indent=0):
    for entry in os.listdir(dirname):
        entry = os.path.join(dirname, entry)
        for i in range(r):
            if os.path.isdir(entry):
                runCommand(setdircommand.format(i, entry),
                           indent*' ',
                           True, True, False)
                runCommand(getdircommand.format(entry), indent*' ',
                           True, False, True)
                print
                rectest(entry, i+1, indent+4)
            else:
                runCommand(setfcommand.format(i, entry), indent*' ',
                           True, True, False)
                runCommand(getfcommand.format(entry), indent*' ',
                           True, False, True)
                print
    print


def test_chmack():
    print
    rectest(ROOTDIR)
    print 80*'*'
