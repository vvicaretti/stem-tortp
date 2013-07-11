#!/usr/local/bin/python

"""
TORtp is a simple way to implement
Tor Transparent Proxy in our
GNU/Linux Box

TORtp use TOR's control port for setup
Transparen Proxy and DNS server capability
on TOR, without override default configuration file
with a custom torrc
"""

import argparse
import subprocess
import os
import pynotify
import stem
from stem.control import Controller
import stem.util
import stem.process
from shutil import copy2
import sys

stem.util.system.set_process_name("TORtp")

def notify(title, message):
    pynotify.init("TORtp")
    notice = pynotify.Notification(title, message, "./icon/anonymous.ico")
    notice.show()
    return

def check_user():
   """ Only root can do that! """
   uid = subprocess.Popen('id -u', shell=True, stdout = subprocess.PIPE)
   out = uid.stdout.read()
   if int(out) == 0:
      return os.environ['SUDO_UID']
   else:
      notify("TORtp", "Only root can do that!")
      sys.exit(1)

def set_home(user):
   """ Set user home path"""
   h = subprocess.Popen('egrep "%s:" /etc/passwd | cut -d : -f 6' % user, shell=True, stdout = subprocess.PIPE)
   home = h.stdout.read()
   return home.strip()

def tortp_dir(home):
   """ Create /home/$user/.tortp """
   tortpdir = "%s/.tortp" % home
   if not os.path.exists(tortpdir):
      os.makedirs(tortpdir)
      notify("TORtp", "Directory %s created" % tortpdir)
   return tortpdir

def iptables_clean():
   """ This function remove all iptables rules """
   subprocess.call('iptables -F', shell=True)
   subprocess.call('iptables -X', shell=True)
   subprocess.call('iptables -t nat -F', shell=True)
   subprocess.call('iptables -t nat -X', shell=True)

def iptables_up(tortpdir, user):
   subprocess.call('iptables-save > %s/%s' % (tortpdir, "iptables.txt"), shell=True)
   # Redirect DNSTor port (9053)
   subprocess.call('iptables -t nat -A OUTPUT ! -o lo -p udp -m owner --uid-owner %s -m udp --dport 53 -j REDIRECT --to-ports 9053' % user, shell=True)
   subprocess.call('iptables -t filter -A OUTPUT -p udp -m owner --uid-owner %s -m udp --dport 53 -j ACCEPT' % user, shell=True)
   subprocess.call('iptables -t filter -A OUTPUT -p tcp -m owner --uid-owner %s -m tcp --dport 53 -j ACCEPT' % user, shell=True)
   # Redirect to Transparent Proxy Tor (9040)
   subprocess.call('iptables -t nat -A OUTPUT ! -o lo -p tcp -m owner --uid-owner %s -m tcp -j REDIRECT --to-ports 9040' % user, shell=True)
   subprocess.call('iptables -t filter -A OUTPUT -p tcp -m owner --uid-owner %s -m tcp --dport 9040 -j ACCEPT' % user, shell=True)
   subprocess.call('iptables -t filter -A OUTPUT ! -o lo -m owner --uid-owner %s -j DROP' % user, shell=True)
   subprocess.call('iptables -t nat -A OUTPUT -p tcp -m owner --uid-owner %s -m tcp --syn -d 127.0.0.1 --dport 9051 -j ACCEPT' % user, shell=True)
   notify("TORtp", "Tor DNS enabled")

def iptables_down():
   subprocess.call('iptables-restore < %s/%s' % (tortpdir, "iptables.txt"), shell=True)

def resolvconf(tortpdir):
   try:
      copy2("/etc/resolv.conf",tortpdir)
   except IOError as e:
      print e
   resolv = open('/etc/resolv.conf', 'w')
   resolv.write('nameserver 127.0.0.1\n')

def enable_dns_torify(tortpdir):
   try:
      with Controller.from_port(port = 9051) as controller:
         controller.authenticate()
         controller.set_options({"DNSPort": "9053", "AutomapHostsOnResolve": "1"})
         notify("TORtp", "Tor DNS enabled")
   except stem.SocketError:
      stem.process.launch_tor_with_config(config = {'ControlPort': '9051', 'CookieAuthentication': '1'},)
      with Controller.from_port(port = 9051) as controller:
         controller.authenticate()
         controller.set_options({"DNSPort": "9053", "AutomapHostsOnResolve": "1"})
         notify("TORtp", "Tor DNS enabled")

def enable_torproxy():
   try:
      with Controller.from_port(port = 9051) as controller:
         controller.authenticate()
         controller.set_options({"VirtualAddrNetwork": "10.192.0.0/10", "TransPort": "9040", "TransListenAddress": "127.0.0.1","AvoidDiskWrites": "1", "WarnUnsafeSocks": "1"})
         notify("TORtp", "Tor Proxy enabled")
   except stem.SocketError:
       stem.process.launch_tor_with_config(config = {'ControlPort': '9051', 'CookieAuthentication': '1'},)
       with Controller.from_port(port = 9051) as controller:
          controller.authenticate()
          controller.set_options({"VirtualAddrNetwork": "10.192.0.0/10", "TransPort": "9040", "TransListenAddress": "127.0.0.1","AvoidDiskWrites": "1", "WarnUnsafeSocks": "1"})
          notify("TORtp", "Tor Proxy enabled")

def start(tortpdir):
   enable_dns_torify(tortpdir)
   enable_torproxy()
   resolvconf(tortpdir)
   iptables_clean()
   iptables_up(tortpdir, check_user())

def stop(tortpdir):
   pass

def main(arg):
   parser = argparse.ArgumentParser()
   parser.add_argument("do", help="start o stop?")
   args = parser.parse_args()
   if args.do == "start":
      tortpdir = tortp_dir(set_home(check_user()))
      start(tortpdir)
   if args.do == "stop":
      ortpdir = tortp_dir(set_home(check_user()))
      stop()
   if args.do != "start" and args.do != "stop":
      print 'Type "tortp.py -h" for options'

   # 6. check se sto usando tor

if __name__ == '__main__':
   main(sys.argv[1:])
