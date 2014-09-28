#!/usr/bin/env python

"""
TorTP is a simple way to implement
Tor Transparent Proxy in our GNU/Linux Box

TorTP use Tor's control port for setup
Transparen Proxy and DNS server capability
on TOR, without override default configuration file
with a custom torrc
"""

import subprocess
import os
import stem
from stem.control import Controller
from stem.version import get_system_tor_version
import stem.util
from stem.util import system
import stem.process
from stem import CircStatus
from shutil import copy2
import sys
import pwd
import urllib
import re

def notify(title, message):
    """
    Notification system
    """
    print("[%s]: %s" % (title, message))
    return

def check_user():
   """
   Only root can do that!
   """
   uid = os.getuid()
   if uid == 0:
      return os.environ['SUDO_UID']
   else:
      notify("TorTP", "[!] Only root can do that!")
      sys.exit(1)

def get_toruser():
    """
    Get tor username
    """
    pid = system.get_pid_by_name("tor")
    toruser = system.get_user(pid)
    return toruser

def get_home(user):
   """
   Get user home path
   """
   return pwd.getpwuid(int(user))[5]

def tortp_dir(home):
   """
   Create directory /home/$user/.tortp
   """
   tortpdir = "%s/.tortp" % home
   if not os.path.exists(tortpdir):
      os.makedirs(tortpdir)
      notify("TorTP", "[+] Directory %s created" % tortpdir)
   return tortpdir

def check_sys_dependencies():
   """
   Check if all dependencies are installed
   """
   devnull = open(os.devnull,"w")
   dnsmasq = subprocess.call(["dpkg","-s","dnsmasq"],stdout=devnull,stderr=subprocess.STDOUT)
   if dnsmasq != 0:
      notify("TorTP", "[!] Dnsmasq is not installed")
      sys.exit(1)
   tor = subprocess.call(["dpkg","-s","tor"],stdout=devnull,stderr=subprocess.STDOUT)
   if tor != 0:
      notify("TorTP", "[!] Tor is not installed")
      sys.exit(1)
   wipe = subprocess.call(["dpkg", "-s", "wipe"],stdout=devnull,stderr=subprocess.STDOUT)
   if wipe != 0:
       notify("TorTP", "[!] Wipe is not installed")
       sys.exit(1)
   devnull.close()


def wipe_tor_log():
   """
   Remove Tor logs when TorTP is closed
   """
   devnull = open(os.devnull,"w")
   wipelog = subprocess.call(["wipe", "-f", "-s", "-q", "/var/log/tor/log"],stdout=devnull,stderr=subprocess.STDOUT)
   if wipelog == 0:
       notify("TorTP", "[+] Log wiped")
   devnull.close()

def iptables_clean():
   """
   This function remove all iptables rules
   """
   subprocess.call(['iptables', '-F'])
   subprocess.call(['iptables', '-X'])
   subprocess.call(['iptables', '-t', 'nat', '-F'])
   subprocess.call(['iptables', '-t', 'nat', '-X'])

def iptables_up(tortpdir, toruser):
   """
   This function make backup and add iptables rules for redirect all network traffic to TorTP.
   Only except with debian-tor user.
   """
   ipt = open("%s/iptables.txt" % tortpdir, "w")
   subprocess.call(['iptables-save'], stdout=ipt)
   ipt.close()
   # Redirect DNSTor port (9053)
   subprocess.call(['iptables', '-t', 'nat', '-A', 'OUTPUT', '!', '-o', 'lo', '-p', 'udp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'udp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', '9053'])
   subprocess.call(['iptables', '-t', 'filter', '-A', 'OUTPUT', '-p', 'udp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'udp', '--dport', '53', '-j', 'ACCEPT'])
   subprocess.call(['iptables', '-t', 'filter', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'tcp', '--dport', '53', '-j', 'ACCEPT'])
   # Redirect to Transparent Proxy Tor (9040)
   subprocess.call(['iptables', '-t', 'nat', '-A', 'OUTPUT', '!', '-o', 'lo', '-p', 'tcp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'tcp', '-j', 'REDIRECT', '--to-ports', '9040'])
   subprocess.call(['iptables', '-t', 'filter', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'tcp', '--dport', '9040', '-j', 'ACCEPT'])
   subprocess.call(['iptables', '-t', 'filter', '-A', 'OUTPUT', '!', '-o', 'lo', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-j', 'DROP'])
   subprocess.call(['iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'owner', '!', '--uid-owner', '%s' % toruser, '-m', 'tcp', '--syn', '-d', '127.0.0.1', '--dport', '9051', '-j', 'ACCEPT'])

def iptables_down(tortpdir):
   """
   Restore original iptables rules
   """
   try:
      subprocess.call('iptables-restore < %s/iptables.txt' % tortpdir, shell=True)
      os.remove("%s/iptables.txt" % tortpdir)
   except IOError as e:
      iptables_clean()
      print e

def resolvconf(tortpdir):
   """
   Backup and modify resolv configuration file
   """
   try:
      copy2("/etc/resolv.conf",tortpdir)
   except IOError as e:
      print e
   resolv = open('/etc/resolv.conf', 'w')
   resolv.write('nameserver 127.0.0.1\n')
   resolv.close()

def dnsmasq(tortpdir):
   """
   Backup and modify dnsmasq configuration file
   """
   try:
      copy2("/etc/dnsmasq.conf",tortpdir)
   except IOError as e:
      print e
   dmasq = open('/etc/dnsmasq.conf', 'w')
   dmasq.write('no-resolv\n')
   dmasq.write('server=127.0.0.1#9053\n')
   dmasq.write('listen-address=127.0.0.1\n')
   dmasq.close()

def myip():
   """
   Get my IP from check.torproject.org
   """
   url = "http://check.torproject.org"
   request = urllib.urlopen(url).read()
   myip = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}", request)
   return myip[0]

def check_tortp(myip, exit):
   """
   Check if my IP is a Tor exit node
   """
   if system.is_running("tor"):
      try:
         if myip not in exit['ipaddress']:
            notify("TorTP", "[-] Sorry. TorTP is not working: %s" % myip)
            sys.exit(1)
      except stem.SocketError as exc:
         notify("TorTP", "[!] Unable to connect to port 9051 (%s)" % exc)
         sys.exit(1)

      notify("TorTP", "[+] Congratulations. TorTP is working: %s" % myip)
      return myip
   else:
      notify("TorTP", "[!] Tor is not running")
      sys.exit(3)

def enable_tordns():
   """
   Use Tor ControlPort for enable TorDNS
   """
   with Controller.from_port(port = 9051) as controller:
      controller.authenticate()
      controller.set_options({"DNSPort": "9053", "DNSListenAddress": "127.0.0.1", "AutomapHostsOnResolve": "1", "AutomapHostsSuffixes": ".exit,.onion"})

def enable_torproxy():
   """
   Use Tor ControlPort for enable Tor Transparent Proxy
   """
   with Controller.from_port(port = 9051) as controller:
      controller.authenticate()
      controller.set_options({"VirtualAddrNetwork": "10.192.0.0/10", "TransPort": "9040", "TransListenAddress": "127.0.0.1","AvoidDiskWrites": "1", "WarnUnsafeSocks": "1"})

def get_exit():
   """
   Get list of exit node from stem
   """
   if system.is_running("tor"):
      try:
         with Controller.from_port(port = 9051) as controller:
            controller.authenticate()
            exit = {'count': [], 'fingerprint': [], 'nickname': [], 'ipaddress': []}
            count = -1
            for circ in controller.get_circuits():
               if circ.status != CircStatus.BUILT:
                  continue
               exit_fp, exit_nickname = circ.path[-1]
               exit_desc = controller.get_network_status(exit_fp, None)
               exit_address = exit_desc.address if exit_desc else 'unknown'
               count += 1
               exit['count'].append(count)
               exit['fingerprint'].append(exit_fp)
               exit['nickname'].append(exit_nickname)
               exit['ipaddress'].append(exit_address)
         return exit
      except stem.SocketError as exc:
         notify("TorTP", "[!] Unable to connect to port 9051 (%s)" % exc)
         sys.exit(1)
   else:
      notify("TorTP", "[!] Tor is not running")


def exit_info(exit):
   """
   Print info about my exit node
   """
   torversion = get_system_tor_version()
   print "Tor version: %s\n" % torversion
   for i in exit['count']:
      print "  nickname: %s" % exit['nickname'][i]
      print "  address: %s" % exit['ipaddress'][i]
      print "  fingerprint: %s\n" % exit['fingerprint'][i]

def tor_new():
   """
   Create a new tor circuit
   """
   try:
      stem.socket.ControlPort(port = 9051)
   except stem.SocketError as exc:
      notify("TorTP", "[!] Unable to connect to port 9051 (%s)" % exc)
      sys.exit(1)
   with Controller.from_port(port = 9051) as controller:
      controller.authenticate()
      controller.signal(stem.Signal.NEWNYM)
      notify("TorTP", "[+] New Tor circuit created")

def start(tortpdir):
   """
   Start TorTP
   """
   if system.is_running("tor"):
      try:
         stem.socket.ControlPort(port = 9051)
      except stem.SocketError as exc:
         notify("TorTP", "[!] Unable to connect to port 9051 (%s)" % exc)
         sys.exit(1)
      if os.path.exists("%s/resolv.conf" % tortpdir) and os.path.exists("%s/dnsmasq.conf" % tortpdir) and os.path.exists("%s/iptables.txt" % tortpdir):
         notify("TorTP", "[!] TorTP is already running")
         sys.exit(2)
      else:
         check_sys_dependencies()
         iptables_clean()
         iptables_up(tortpdir, get_toruser())
         enable_tordns()
         enable_torproxy()
         resolvconf(tortpdir)
         dnsmasq(tortpdir)
         devnull = open(os.devnull,"w")
         subprocess.call(['/etc/init.d/dnsmasq', 'restart'], stdout=devnull)
         devnull.close()
         notify("TorTP", "[+] Tor Transparent Proxy enabled")
   else:
      notify("TorTP", "[!] Tor is not running")
      sys.exit(3)

def stop(tortpdir):
   """
   Stop TorTP and restore original network configuration
   """
   try:
      copy2("%s/resolv.conf" % tortpdir, "/etc")
      copy2("%s/dnsmasq.conf" % tortpdir, "/etc")
      os.remove("%s/resolv.conf" % tortpdir)
      os.remove("%s/dnsmasq.conf" % tortpdir)
   except IOError:
      notify("TorTP", "[!] TorTP seems already disabled")
      sys.exit(1)
   devnull = open(os.devnull,"w")
   subprocess.call(['/etc/init.d/dnsmasq', 'restart'], stdout=devnull)
   subprocess.call(['/etc/init.d/tor', 'reload'], stdout=devnull)
   devnull.close()
   iptables_down(tortpdir)
   notify("TorTP", "[+] Tor Transparent Proxy disabled")
   wipe_tor_log()

def is_running():
   """
   check if TorTP is running
   """
   #TODO: change check
   path = tortp_dir(get_home(check_user()))
   file_path = os.path.join(path, "resolv.conf")
   return os.path.exists(file_path)

def do_start():
   start(tortp_dir(get_home(check_user())))

def do_stop():
   stop(tortp_dir(get_home(check_user())))

def do_check():
   return check_tortp(myip(), get_exit())
