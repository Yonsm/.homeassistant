
#!/bin/sh

hdparm -I /dev/sda
hdparm -B 127 /dev/sda
hdparm -S 180 /dev/sda
hdparm -I /dev/sda
hdparm -C /dev/sda
# Cause Boot Failure: echo "/dev/sda1 /mnt ntfs defaults,noatime,nodiratime 0 0" >> /etc/fstab
sed -i 's/exit 0/mount \/dev\/sda1 \/mnt\nexit 0/'  /etc/rc.local
#reboot

apt install samba samba-vfs-modules
smbpasswd -a admin

cat <<\EOF > /etc/samba/smb.conf
[global]
# General
netbios name = Store
#workgroup = WORKGROUP
server string = Storage
unix charset = UTF-8
# interfaces = lo eth0
# bind interfaces only = yes

# Account
passdb backend = smbpasswd
map to guest = Bad User
access based share enum = yes

# Content
veto files = /Thumbs.db/.DS_Store/._.DS_Store/.apdisk/
force create mode = 0644
force directory mode = 0755
load printers = no
disable spoolss = yes

# Connection
deadtime = 15
min receivefile size = 16384
write cache size = 524288
socket options = TCP_NODELAY IPTOS_LOWDELAY
aio read size = 16384
aio write size = 16384
use sendfile = yes

# Mac OS
min protocol = SMB2
ea support = yes
#mdns name = mdns
vfs objects = catia fruit streams_xattr
fruit:aapl = yes
fruit:model = Xserve
readdir_attr:aapl_rsize = yes
readdir_attr:aapl_finder_info = yes
readdir_attr:aapl_max_access = yes
fruit:nfs_aces = yes
fruit:copyfile= yes
fruit:metadata = netatalk
fruit:resource = file
fruit:locking = none
fruit:encoding = private
unix extensions = yes
spotlight = no
smb2 max read = 8388608
smb2 max write = 8388608
smb2 max trans = 8388608
smb2 leases = yes
kernel oplocks = no
strict sync = yes
sync always = no
delete veto files = true
fruit:posix_rename = yes
fruit:veto_appledouble = yes
fruit:zero_file_id = yes
fruit:wipe_intentionally_left_blank_rfork = yes
fruit:delete_empty_adfiles = yes


[Downloads]
path = /mnt/Downloads
public = yes
writable = yes

[Public]
path = /mnt/Public
public = yes
write list = admin

[Music]
path = /mnt/Music
public = yes
write list = admin

[Pictures]
path = /mnt/Pictures
public = yes
write list = admin

[Movies]
path = /mnt/Movies
public = yes
write list = admin

[Documents]
path = /mnt/Documents
public = no
writable = yes
valid users = admin

EOF

#smbd -F --no-process-group -S -d=3
systemctl restart smbd
