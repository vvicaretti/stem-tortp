TorTP
==========

TorTP will change your iptables configuration to force all TCP traffic to pass through Tor (and also UDP DNS request). The network traffic that is not capable of passing through Tor (such as UDP or ICMP) is just dropped.

TorTP use python-stem library for setup Transparen Proxy and DNS server capability on Tor, without override Tor default configuration file.

HowTo install:
=============

Add freepto repository:

<code>$ wget http://deb.freepto.mx/deb.gpg</code>

<code>$ cat deb.gpg | apt-key add -</code>

<code>$ echo "deb http://deb.freepto.mx/freeptorepo berenjena main" > /etc/apt/sources.list.d/freepto.list</code>

Install:

<code>sudo apt-get install tortp python-tortp</code>

Enable Tor Control Port:

<code>sed -i 's/#ControlPort 9051/ControlPort 9051/' /etc/tor/torrc</code>

Install GUI (optional):

<code>apt-get install tortp-gtk</code>

HowTo user TorTP:
=================

<code>$ sudo tortp -h</code>

<code>$ man tortp</code>
