import pytest
import subprocess
import sys
import os
from StringIO import StringIO

ROOTDIR = '/testfs'
FNULL = open(os.devnull, 'w')
filesystems = ('xfs', 'ntfs', 'exfat')
subdirs = ('dir', 'subdir')


def stRes(res):
    return '...SUCSESS' if res == 0 else "...FAIL"


def runCommand(command, supress=False):
    scommand = command.split()

    if not supress:
        res = subprocess.call(scommand)
    else:
        FNULL = open('/dev/null', 'w')
        res = subprocess.call(scommand, stdout=FNULL, stderr=subprocess.STDOUT)

    return (command if not supress else '') + stRes(res)


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
        runCommand(command, supress=True)

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
            print('fill file...done')

        print 80*'*'

    command = 'sudo pdp-flbl -f 3:0:0xffffffffffffff:ccnr {0}'.format(ROOTDIR)
    runCommand(command)


def teardown_module(module):
    print
    for i, fs in enumerate(filesystems):
        dirname = os.path.join(ROOTDIR, fs)
        res = subprocess.call(['sudo', 'fusermount', '-u', dirname])
        print 'umount {0}...{1}'.format(dirname, stRes(res))

        command = ['sudo', 'blockdev', '--flushbufs',  '/dev/ram{0}'.format(i)]
        res = subprocess.call(command)
        print 'clean fs {0} ...{1}'.format(dirname, stRes(res))

    res = subprocess.call(['sudo', 'rm', '-rf', ROOTDIR])
    print 'remove {0}...{1}'.format(ROOTDIR, stRes(res))


def test_init():
    print 80*'*'
    assert True


dircommand = ('sudo pdp-flbl {0}:0:0xffffffffffffff:ccnr {1}')
fcommand = 'sudo pdp-flbl {0} {1}'


def rectest(dirname, r=4, indent=0):
    for entry in os.listdir(dirname):
        entry = os.path.join(dirname, entry)
        for i in range(r):
            if os.path.isdir(entry):
                print indent*' ', 'set:', entry, i, \
                    runCommand(dircommand.format(i, entry), True)
                rectest(entry, i+1, indent+4)
            else:
                print indent*' ', 'set:', entry, i, \
                    runCommand(fcommand.format(i, entry), True)


def test_chmack():
    print
    rectest(ROOTDIR)
    print 80*'*'
