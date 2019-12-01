#!/usr/bin/env python3

#This script is designed to be as small and simple as possible so that it can be easily run over ssh

import os
import subprocess
import sys

snapshot_mount_point="/mnt"
zfs='/usr/sbin/zfs'
zpool='/usr/sbin/zpool'
snapshot_name="backup"

def get_mounts():
    with open('/proc/mounts', 'r') as f:
        mounts = f.readlines()
        mount_dict = {}
        for mount in mounts:
            fields = mount.split()
            mount_dict[fields[0]] = fields[1]
    return mount_dict

def get_snapshots():
    zfs_command = subprocess.Popen([zfs, 'list', '-t', 'snap', '-H'], stdin=None, stdout=subprocess.PIPE, stderr=None, shell=None)
    return [line.decode() for line in zfs_command.stdout.readlines()]

def get_pools():
    zpool_command = subprocess.Popen(["/usr/sbin/zpool", "list", "-H"], stdin=None, stdout=subprocess.PIPE, stderr=None, shell=None)
    return [line.decode() for line in zpool_command.stdout.readlines()]


if sys.argv[1] == "create":
    try:
        os.mkdir(snapshot_mount_point)
    except:
        pass

    for pool in get_pools():
        pool_name = pool.split('\t')[0]
        print("creating snapshots for: {}".format(pool_name))
        try:
            subprocess.check_call([zfs, 'snapshot', "{}@{}".format(pool_name, snapshot_name), '-r'], shell=None)
        except Exception as e:
            print("exception {}".format(e))
            sys.exit(1)

    mount_dict = get_mounts()
    snapshots = get_snapshots()

    mount_points = {}
    for filesystem in snapshots:
        filesystem_name = filesystem.rstrip().split()[0]
        original_filesystem = filesystem_name.replace('@{}'.format(snapshot_name), '')
        if original_filesystem in mount_dict:
            mount_point = mount_dict[original_filesystem]
            mount_points[os.path.normpath("{}/{}".format(snapshot_mount_point, mount_point))] = filesystem_name

    mounts = list(mount_points.items())
    mounts.sort(key=lambda t: len(t[0]))

    for i in mounts:
        print("Mounting: {} to {}".format(i[0], i[1]))
        subprocess.check_call(['/usr/bin/mount', '-t', 'zfs', i[1], i[0]], shell=None)

elif sys.argv[1] == "destroy":
    print("Unmounting: {}".format(snapshot_mount_point))
    subprocess.call(["/usr/bin/umount", "-R", snapshot_mount_point])

    for pool in get_pools():
        pool_name = pool.split('\t')[0]
        print("Destroying snapshots for {}".format(pool_name))
        try:
            subprocess.check_call([zfs, 'destroy', "{}@{}".format(pool_name, snapshot_name), '-r'], shell=None)
        except Exception as e:
            print("exception {}".format(e))
            sys.exit(1)
