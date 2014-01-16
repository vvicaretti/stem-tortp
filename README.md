TorTP
==========

TorTP will change your iptables configuration to force all traffic originating from a certain user to pass through Tor. The traffic that is not capable of passing through Tor (such as UDP or ICMP) is just dropped. 

TorTP use python-stem library for setup Transparen Proxy and DNS server capability on Tor, without override Tor default configuration file.
