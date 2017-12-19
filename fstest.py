import pytest
import subprocess
import os

ROOTDIR = '/testfs'
FNULL = open(os.devnull, 'w')
filesystems = ('xfs', 'ntfs', 'exfat')
subdirs = ('dir', 'subdir')


def stRes(res):
    return 'SUCSESS' if res == 0 else "FAIL"


def setup_module(module):
    print("\n...basic setup into this module")

    res = subprocess.call(['sudo', 'mkdir', ROOTDIR])
    print 'create test root dir...{0}'.format(stRes(res))

    res = subprocess.call(['sudo', 'chown', 'user:disk', ROOTDIR])
    print 'chown test root dir ...{0}'.format(stRes(res))
    print 80*'*'

    for i, fs in enumerate(filesystems):
        dirname = os.path.join(ROOTDIR, fs)

        res = subprocess.call(['sudo', 'mkdir', '-p', dirname])
        print 'create {0}...{1}'.format(dirname, stRes(res))

        command = ['sudo', 'mkfs.{0}'.format(fs), '/dev/ram{0}'.format(i)]
        res = subprocess.call(command, stdout=FNULL, stderr=subprocess.STDOUT)
        print 'mkfs.{0} in /dev/ram{1}...{2}'.format(fs, i, stRes(res))

        command = ['sudo', 'mount', '/dev/ram{0}'.format(i), dirname]
        res = subprocess.call(command)
        print 'mount fs {0} to {1}...{2}'.format(fs, dirname, stRes(res))

        subdirname = dirname
        for subdir in subdirs:
            subdirname = os.path.join(subdirname, subdir)
        command = ['sudo', 'mkdir', '-p', subdirname]
        res = subprocess.call(command)
        print 'create test subdirs...{0}'.format(stRes(res))

        command = ['sudo', 'chown', '-R', 'user:disk', dirname]
        res = subprocess.call(command)
        print 'chown for {0} ... {1}'.format(dirname, stRes(res))

        with open(os.path.join(subdirname, 'testfile.txt'), 'w') as f:
            f.write('This is a test file...\n')

        print 80*'*'

    command = ['sudo', 'pdp-flbl', '-f', '3:0:0xffffffffffffff:ccnr', ROOTDIR]
    res = subprocess.call(command)
    print 'set mac to test root dir ... {0}'.format(stRes(res))


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


def rectest(dirname, r=4):
    for i in range(r):
        dircommand = ['sudo', 'pdp-flbl',
                      '{0}:0:0xffffffffffffff:ccnr'.format(i), dirname]
        res = subprocess.call(dircommand)
        print 'set mac {0} level to {1} ...{2}'.format(i, dirname, stRes(res))
        for sub in os.listdir(dirname):
            entry = os.path.join(dirname, sub)
            if os.path.isdir(entry):
                rectest(entry, i)
            else:
                for i in range(r):
                    fcommand = ['sudo', 'pdp-flbl', '{0}'.format(i), entry]
                    res = subprocess.call(fcommand)
                    print 'set mac {0} level to {1} ...{2}'.format(i,
                                                                   entry,
                                                                   stRes(res))


def test_chmack():
    rectest(ROOTDIR)
