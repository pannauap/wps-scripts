#!/usr/bin/env python
"""Network interface and MAC address management utilities.

Consolidates interface discovery, monitor mode, and MAC changing from
reaver-spoof.py and pyxiewps variants.
"""

import subprocess
from os import system
from random import randint
from re import search, sub

from shared_utils.process import exec_cmd


def random_mac():
    """Generate a random MAC address with Xen OUI prefix (00:16:3e)."""
    mac = [0x00, 0x16, 0x3e,
           randint(0x00, 0x7f),
           randint(0x00, 0xff),
           randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def change_mac(iface, mac=None):
    """Bring interface down, set MAC address, bring it back up.

    Args:
        iface: interface name (e.g. 'wlan0').
        mac: MAC string to set, or None to use a random MAC.

    Returns:
        str: the MAC address that was set.
    """
    exec_cmd('ifconfig %s down' % iface)
    if mac is None:
        mac = random_mac()
    exec_cmd('ifconfig %s hw ether %s' % (iface, mac))
    exec_cmd('ifconfig %s up' % iface)
    return mac


def change_mac_with_macchanger(iface_mon):
    """Change MAC using macchanger (used by pyxiewps scripts).

    Args:
        iface_mon: monitor-mode interface name.

    Returns:
        str: the new MAC address (uppercased).
    """
    system('ifconfig %s down' % iface_mon)
    system('iwconfig %s mode Managed' % iface_mon)
    system('ifconfig %s up' % iface_mon)
    system('ifconfig %s down' % iface_mon)
    mac = subprocess.check_output(['macchanger', '-r', iface_mon])
    mac = mac.split('\n')[2]
    mac = sub('New       MAC\: ', '', mac.strip())
    mac = sub(' \(unknown\)', '', mac)
    system('ifconfig %s up' % iface_mon)
    system('ifconfig %s down' % iface_mon)
    system('iwconfig %s mode monitor' % iface_mon)
    system('ifconfig %s up' % iface_mon)
    return mac.upper()


def discover_interfaces():
    """Discover wireless interfaces and monitor-mode interfaces via iwconfig.

    Returns:
        tuple: (monitors, interfaces) where monitors is a list of monitor-mode
        interface names, and interfaces is a dict mapping iface name to
        1 (associated) or 0 (not associated).
    """
    monitors = []
    interfaces = {}
    proc = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print('Warning: iwconfig failed (rc=%d)' % proc.returncode)
        if stderr:
            print('  stderr: %s' % stderr.strip())
    for line in stdout.split('\n'):
        if len(line) == 0:
            continue
        if line[0] != ' ':
            wired_search = search('eth[0-9]|em[0-9]|p[1-9]p[1-9]', line)
            if not wired_search:
                iface = line[:line.find(' ')]
                if 'Mode:Monitor' in line:
                    monitors.append(iface)
                elif 'IEEE 802.11' in line:
                    if "ESSID:\"" in line:
                        interfaces[iface] = 1
                    else:
                        interfaces[iface] = 0
    return monitors, interfaces


def start_monitor(iface):
    """Enable monitor mode on an interface using airmon-ng."""
    print('Starting mon on %s' % iface)
    exec_cmd('airmon-ng start %s' % iface)


def stop_monitor(iface):
    """Disable monitor mode on an interface using airmon-ng."""
    print('Stopping mon on %s' % iface)
    exec_cmd('airmon-ng stop %s' % iface)
