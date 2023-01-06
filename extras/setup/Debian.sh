#!/bin/sh

# 
apt install adb
mkdir -p /opt/bin; cd /opt/bin
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-5.1.1-amd64-static/ffmpeg .
mv ffmpeg-5.1.1-amd64-static/ffprobe .
mv ffmpeg-5.1.1-amd64-static/model .
mv ffmpeg-5.1.1-amd64-static/qt-faststart .
rm -rf ffmpeg-5.1.1-amd64-static
rm ffmpeg-release-amd64-static.tar.xz

# ============================== Bridge ==============================
sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0"/' /etc/default/grub
cat <<\EOF > /etc/network/interfaces
#source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

#allow-hotplug eth0
#iface eth0 inet dhcp
iface eth0 inet manual
iface eth1 inet manual
iface eth2 inet manual
iface eth3 inet manual

auto br0
#iface br0 inet dhcp
iface br0 inet static
	address 192.168.1.2
	broadcast 192.168.1.255
	netmask 255.255.255.0
	gateway 192.168.1.1
	dns-nameservers 192.168.1.1
	bridge_ports eth0 eth1 eth2 eth3
	bridge_stp on
	bridge_waitport 0
	bridge_fd 0
EOF
grub-mkconfig -o /boot/grub/grub.cfg

# ============================== Samba ==============================
apt install samba
cat <<\EOF > /etc/samba/smb.conf
[global]
# General
netbios name = Store
server string = Storage
#interfaces = lo br0
#bind interfaces only = yes

# Account
passdb backend = smbpasswd
map to guest = Bad User
access based share enum = yes

# Content
force create mode = 0644
force directory mode = 0755
load printers = no
disable spoolss = yes

# Connection
deadtime = 30
min receivefile size = 16384
#socket options = TCP_NODELAY IPTOS_LOWDELAY
aio read size = 16384
aio write size = 16384
use sendfile = yes
#min protocol = SMB2
#max protocol = SMB3
#max connections = 100

# Mac OS
#mdns name = mdns
delete veto files = yes
veto files = /Thumbs.db/.DS_Store/._.DS_Store/.apdisk/
vfs objects = fruit
fruit:model = Xserve
fruit:copyfile = yes

[Documents]
path = /mnt/STORE/Documents
public = no
writable = yes
valid users = admin

[Downloads]
path = /mnt/STORE/Downloads
public = yes
writable = yes

[Movies]
path = /mnt/STORE/Movies
public = yes
write list = admin

[Music]
path = /mnt/STORE/Music
public = yes
write list = admin

[Pictures]
path = /mnt/STORE/Pictures
public = yes
write list = admin

[Public]
path = /mnt/STORE/Public
public = yes
write list = admin

EOF

# KODI: NOT WORKED on Debian 11!  Worked on PVE 7.5
# https://blog.d2okkk.net/202104/j1800_setup_2/
apt-get update
#apt-get install ca-certificates curl gnupg
#curl 'https://basilgello.github.io/kodi-nightly-debian-repo/repository-key.asc' | apt-key add -
apt-get install --install-recommends kodi kodi-pvr-iptvsimple
apt-get install software-properties-common xorg xserver-xorg-legacy alsa-utils mesa-utils git-core librtmp1 libmad0 lm-sensors libmpeg2-4 avahi-daemon libva2 vainfo i965-va-driver dbus-x11 pastebinit xserver-xorg-video-intel
apt-get upgrade

cat <<\EOF > /etc/X11/Xwrapper.config
allowed_users=anybody
needs_root_rights=yes
EOF

cat <<\EOF > /etc/systemd/system/kodi.service
[Unit]
Description = kodi-standalone using xinit
After = remote-fs.target systemd-user-sessions.service mysql.service

[Service]
#User = kodi
#Group = kodi
Type = simple
ExecStart = /usr/bin/xinit /usr/bin/dbus-launch /usr/bin/kodi-standalone -- :0 -nolisten tcp
#Restart = always
#RestartSec = 30

[Install]
WantedBy = multi-user.target
EOF

systemctl daemon-reload
systemctl enable kodi
adduser kodi
usermod -a -G cdrom,audio,video,plugdev,users,dialout,dip,input kodi
