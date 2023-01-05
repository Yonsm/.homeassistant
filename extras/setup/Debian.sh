#!/bin/sh

# ============================== Alias ==============================
cat <<\EOF >> ~/.bashrc
export LS_OPTIONS='--color=auto'
#eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls $LS_OPTIONS -l'
alias l='ls $LS_OPTIONS -lA'

alias mqttsub='mqttsub() { mosquitto_sub -v -t "$1#"; }; mqttsub'
alias mqttre='systemctl stop mosquitto; sleep 2; rm -rf /var/lib/mosquitto/mosquitto.db; systemctl start mosquitto'
alias hassre='docker restart homeassistant'
alias hasslog='tail -f /home/hass/config/home-assistant.log'
alias hasste='docker exec -it homeassistant /bin/bash'

EOF

# ============================== Mosquitto ==============================
apt install mosquitto mosquitto-clients
echo "listener 1883">>/etc/mosquitto/mosquitto.conf
echo "allow_anonymous true">>/etc/mosquitto/mosquitto.conf

# ============================== Docker ==============================
docker run -d --name homeassistant --privileged --restart=unless-stopped -e TZ=Asia/Shanghai -v /home/hass/config:/config --network=host ghcr.io/home-assistant/home-assistant:stable

# ============================== Samba ==============================
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

# ============================== KODI ==============================
apt-get update
apt-get install ca-certificates curl gnupg
#curl 'https://basilgello.github.io/kodi-nightly-debian-repo/repository-key.asc' | apt-key add -
apt-get install --install-recommends kodi kodi-pvr-iptvsimple
apt-get install software-properties-common xorg xserver-xorg-legacy alsa-utils mesa-utils git-core librtmp1 libmad0 lm-sensors libmpeg2-4 avahi-daemon libva2 vainfo i965-va-driver dbus-x11 samba pastebinit xserver-xorg-video-intel
apt-get upgrade

#https://blog.d2okkk.net/202104/j1800_setup_2/

#编辑/etc/X11/Xwrapper.config 允许anybody启动Xserver，值得注意的是，在Debian里面还需要needs_root_rights=yes。

allowed_users=anybody
needs_root_rights=yes

/etc/systemd/system/kodi.service

[Unit]
Description = kodi-standalone using xinit
After = remote-fs.target systemd-user-sessions.service mysql.service

[Service]
User = kodi
Group = kodi
Type = simple
ExecStart = /usr/bin/xinit /usr/bin/dbus-launch /usr/bin/kodi-standalone -- :0 -nolisten tcp
#Restart = always
#RestartSec = 30

[Install]
WantedBy = multi-user.target

开机自动启动kodi

systemctl daemon-reload
systemctl enable kodi
新建kodi用户，并添加权限

adduser kodi
usermod -a -G cdrom,audio,video,plugdev,users,dialout,dip,input kodi
