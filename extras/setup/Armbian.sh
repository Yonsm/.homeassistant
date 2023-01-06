#!/bin/sh

# ============================== N1 Armbian ==============================
# N1 2022
# https://github.com/ophub/amlogic-s9xxx-armbian
# https://github.com/ophub/amlogic-s9xxx-armbian/releases/download/Armbian_Aml_jammy_08.30.0225/Armbian_22.08.0_Aml_s905d_jammy_5.15.62_server_2022.08.30.img.gz

# Write on macOS
# diskutil list # e.g. /dev/disk3
# diskutil umount /dev/disk3s1
# sudo dd if=armbian.img of=/dev/rdisk3 bs=1M

# ============================== Basic Config ==============================
# tzsleect
# cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# raspi-config # Hostname, WiFi, locales(en_US.UTF-8/zh_CN.GB18030/zh_CN.UTF-8), Timezone
##apt install python3 python3-pip

# MacOS
#ssh root@hass "mkdir ~/.ssh"
#scp ~/.ssh/authorized_keys root@hass:~/.ssh/
#scp ~/.ssh/id_rsa root@hass:~/.ssh/
#scp ~/.ssh/config root@hass:~/.ssh/

# SSH
ssh root@hass "mkdir ~/.ssh"
scp ~/.ssh/authorized_keys root@hass:~/.ssh/
scp ~/.ssh/id_rsa root@hass:~/.ssh/
scp ~/.ssh/config root@hass:~/.ssh/

ssh admin@hass "mkdir ~/.ssh"
scp ~/.ssh/authorized_keys admin@hass:~/.ssh/
scp ~/.ssh/id_rsa admin@hass:~/.ssh/
scp ~/.ssh/config admin@hass:~/.ssh/

sed -i "s/Port 22/Port 89/" /etc/ssh/sshd_config
sed -i "s/#Port 22/Port 89/" /etc/ssh/sshd_config

ssh root@hass

#
echo "admin ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
#echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale

armbian-config #Hostname, wifi,timezone, apt-source
#echo "Asia/Shanghai" > /etc/timezone && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# Speedtest
ln -s /usr/bin/python3 /usr/bin/python
cd /usr/local/bin
wget -O speedtest https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py; chmod +x speedtest; ./speedtest

# nginx
apt install nginx
ln -s /root/.homeassistant/extras/setup/nginx.conf /etc/nginx/sites-enabled/default

#ln -s /root/.homeassistant/extras/setup/adb /usr/local/bin/
ln -s /root/.homeassistant/extras/setup/ffmpeg /usr/local/bin/
ln -s /root/.homeassistant/extras/setup/trojan /usr/local/bin/
ln -s /root/.homeassistant/extras/setup/ss-local /usr/local/bin/
ln -s /root/.homeassistant/extras/setup/ssr-client /usr/local/bin/

# Trojan
#echo '{"run_type":"client","local_addr":"0.0.0.0","local_port":1080,"remote_addr":"xxx","remote_port":443,"password":["***"],"ssl":{"verify":false}}' >> /root/.homeassistant/extras/setup/.trojan.conf
#echo '{"server":"host","server_port":port,"local_address":"0.0.0.0","local_port":1080,"password":"password","method":"aes-256-gcm"}' >> /root/.homeassistant/extras/setup/ss.conf
cat <<EOF > /etc/systemd/system/socks5.service
[Unit]
Description=Socks5 Proxy
After=network-online.target

[Service]
Type=simple
User=root
#ExecStart=/root/.homeassistant/extras/setup/trojan -c /root/.homeassistant/extras/setup/trojan.conf
#ExecStart=/root/.homeassistant/extras/setup/ss-local -c /root/.homeassistant/extras/setup/ss.conf
ExecStart=/root/.homeassistant/extras/setup/ssr-client -c /root/.homeassistant/extras/setup/ssr.conf

[Install]
WantedBy=multi-user.target

EOF

systemctl --system daemon-reload
systemctl enable socks5


# Samba
hdparm -I /dev/sda
hdparm -B 127 /dev/sda
hdparm -S 180 /dev/sda
hdparm -I /dev/sda
hdparm -C /dev/sda
echo -e "LABEL=STORE\t/mnt/STORE\tntfs\t\tdefaults,noatime,nodiratime\t\t\t0 0" >> /etc/fstab
#reboot

apt install samba samba-vfs-modules
smbpasswd -a admin
cat <<\EOF > /etc/samba/smb.conf
# ?
EOF

#smbd -F --no-process-group -S -d=3
/etc/init.d/smbd restart
