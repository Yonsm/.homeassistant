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

# ============================== Home Assistant ==============================
# cat <<\EOF > /etc/apt/sources.list
# deb http://mirrors.aliyun.com/debian/ jammy main non-free contrib
# deb-src http://mirrors.aliyun.com/debian/ jammy main non-free contrib
# deb http://mirrors.aliyun.com/debian-security jammy/updates main
# deb-src http://mirrors.aliyun.com/debian-security jammy/updates main
# deb http://mirrors.aliyun.com/debian/ jammy-updates main non-free contrib
# deb-src http://mirrors.aliyun.com/debian/ jammy-updates main non-free contrib
# deb http://mirrors.aliyun.com/debian/ jammy-backports main non-free contrib
# deb-src http://mirrors.aliyun.com/debian/ jammy-backports main non-free contrib
# EOF

apt update && apt upgrade -y
#apt autoclean
#apt clean
#apt autoremove -y

apt install mosquitto mosquitto-clients libavahi-compat-libdnssd-dev adb telnet python3-pip libpython3.10-dev
echo "listener 1883">>/etc/mosquitto/mosquitto.conf
echo "allow_anonymous true">>/etc/mosquitto/mosquitto.conf

# Armbian
#apt install python3-pip python3-dev python3-setuptools libffi-dev
#ln -sf /usr/bin/python3 /usr/bin/python

# Speedtest
ln -s /usr/bin/python3 /usr/bin/python
cd /usr/local/bin
wget -O speedtest https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py; chmod +x speedtest; ./speedtest

# PIP
##python3 -m pip install --upgrade pip # Logout after install
#curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
#python3 get-pip.py --force-reinstall

# Baidy TTS: pip3 install baidu-aip==1.6.6
#apt install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
#apt install libjpeg-dev zlib1g-dev

# Python 3.9
# apt install build-essential checkinstall
# apt install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
# cd /opt
# wget -o Python.tgz https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
# tar xzf Python.tgz
# cd Python
# ./configure --prefix=/usr --enable-optimizations
# make build_all
# make altinstall
# ln -s /usr/share/pyshared/lsb_release.py /usr/lib/python3.9/site-packages/lsb_release.py
# ln -s /usr/lib/python3/dist-packages/apt_pkg.cpython-37m-aarch64-linux-gnu.so /usr/lib/python3.9/site-packages/apt_pkg.so
# update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1
# update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2
# update-alternatives --config python
# cd /opt && rm -rf Python*

# Home Assistant
pip3 install wheel sqlalchemy
#pip3 install netdisco

pip3 install homeassistant

# Auto start
cat <<EOF > /etc/systemd/system/homeassistant.service
[Unit]
Description=Home Assistant
After=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/hass
Restart=always

[Install]
WantedBy=multi-user.target

EOF

# Debug
hass

systemctl --system daemon-reload
systemctl enable homeassistant
#systemctl start homeassistant


# Alias
cat <<\EOF >> ~/.bashrc
alias l='ls -lA'
alias mqttsub='mqttsub() { mosquitto_sub -v -t "$1#"; }; mqttsub'
alias mqttre='systemctl stop mosquitto; sleep 2; rm -rf /var/lib/mosquitto/mosquitto.db; systemctl start mosquitto'
alias hassre='echo .>~/.homeassistant/home-assistant.log; systemctl restart homeassistant'
alias hasste='systemctl stop homeassistant; hass'
alias hassup='systemctl stop homeassistant; pip3 install homeassistant --upgrade; systemctl start homeassistant'
alias hasslog='tail -f ~/.homeassistant/home-assistant.log'
alias hassrl='hassre; hasslog'

EOF

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


exit 0


# ============================== Samba ==============================

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
