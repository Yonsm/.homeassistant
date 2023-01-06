#!/bin/sh
# Bridge
ip link add name br0 type bridge
ip link set br0 up
ip link set eth0 up
ip link set eth0 master br0
ip addr del 192.168.1.200/24 dev eth0
ip addr add 192.168.1.2/24 dev br0
route add -net default gw 192.168.1.1
ip link set eth1 master br0
ip link set eth2 master br0
ip link set eth3 master br0
