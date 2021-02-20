#!/bin/sh

# ============================== Basic Config ==============================
# Raspberry Pi Only
#ssh pi@hass
# sudo passwd root
# sudo passwd --unlock root
# sudo nano /etc/ssh/sshd_config #PermitRootLogin yes
# sudo mkdir /root/.ssh
# mkdir ~/.ssh
# sudo reboot
# # Raspberry Pi Only: Rename pi->admin
# usermod -l admin pi
# groupmod -n admin pi
# mv /home/pi /home/admin
# usermod -d /home/admin admin
# passwd admin

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

ssh root@hass

#
echo "admin ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale

armbian-config #Hostname, wifi,timezone, apt-source
#echo "Asia/Shanghai" > /etc/timezone && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# ============================== Home Assistant ==============================
apt update && apt upgrade -y
#apt autoclean
#apt clean
#apt autoremove -y

apt install mosquitto mosquitto-clients libavahi-compat-libdnssd-dev libturbojpeg0 adb

# Armbian
apt install python3-pip python3-dev python3-setuptools libffi-dev
ln -sf /usr/bin/python3 /usr/bin/python

# Baidy TTS: pip3 install baidu-aip==1.6.6
apt install libjpeg-dev zlib1g-dev

# Speedtest
cd /usr/local/bin
wget -O speedtest https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py; chmod +x speedtest; ./speedtest

# PIP 18
##python3 -m pip install --upgrade pip # Logout after install
#curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
#python3 get-pip.py --force-reinstall

# Python 3.7+
#curl https://bc.gongxinke.cn/downloads/install-python-latest | bash

# Baidu TTS
#apt install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
#apt install libjpeg-dev zlib1g-dev

# Home Assistant
pip3 install wheel
pip3 install netdisco
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
alias ls='ls $LS_OPTIONS'
alias ll='ls $LS_OPTIONS -l'
alias lla='ls $LS_OPTIONS -la'
alias l='ls $LS_OPTIONS -lA'
alias mqttsub='mosquitto_sub -t "#" -v'
alias mqttre='systemctl stop mosquitto; sleep 2; rm -rf /var/lib/mosquitto/mosquitto.db; systemctl start mosquitto'
alias hassre='echo .>~/.homeassistant/home-assistant.log; systemctl restart homeassistant'
alias hasste='systemctl stop homeassistant; hass'
alias hassup='systemctl stop homeassistant; pip3 install homeassistant --upgrade; systemctl start homeassistant'
alias hasslog='tail -f ~/.homeassistant/home-assistant.log'
EOF

# Trojan
scp trojan root@hass:/usr/local/bin
echo '{"run_type":"client","local_addr":"0.0.0.0","local_port":1080,"remote_addr":"xxx","remote_port":443,"password":["***"],"ssl":{"verify":false}}' >> ~/trojan.conf
cat <<EOF > /etc/systemd/system/trojan.service
[Unit]
Description=Trojan Proxy
After=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/trojan -c /root/trojan.conf

[Install]
WantedBy=multi-user.target

EOF

systemctl --system daemon-reload
systemctl enable trojan


# Install on CoreElec
installentware
opkg update
opkg install gcc make coreutils-expr
opkg install python3-pip python3-setuptools

# libffi-dev
# wget ftp://sourceware.org/pub/libffi/libffi-3.2.1.tar.gz  # 下载包
# tar -zxvf libffi-3.2.1.tar.gz
# cd libffi-3.2.1
# ./configure
# make
# cp armv7l-unknown-linux-gnueabi/include/*.h /opt/include

# Install cryptography
wget http://launchpadlibrarian.net/230019290/libffi-dev_3.2.1-4_arm64.deb # https://launchpad.net/ubuntu/xenial/arm64/libffi-dev/3.2.1-4
scp usr/include/ffitarget.h none:/opt/include
scp usr/include/ffitarget.h none:/opt/include
wget http://launchpadlibrarian.net/413028779/libssl-dev_1.0.2g-1ubuntu4.15_arm64.deb #https://launchpad.net/ubuntu/xenial/arm64/libssl-dev/1.0.2g-1ubuntu4.15
#copy usr/include/openssl/* none:/opt/include/openssl
#copy usr/include/aarch64-linux-gnu/openssl/* none:/opt/include/openssl

ln -s /opt/lib/libffi.so.6.0.4 /opt/lib/libffi.so
ln -s libcrypto.so.1.1 libcrypto.so
ln -s libssl.so.1.1 libssl.so
#pip3 install cryptography

pip3 install wheel homeassistant

systemctl mask kodi
systemctl start kodi
systemctl stop kodi

# Python 3.9
apt install build-essential checkinstall
apt install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
cd /opt
wget -o Python.tgz https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
tar xzf Python.tgz
cd Python
./configure --prefix=/usr --enable-optimizations
make build_all
#make install
make altinstall
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
cd /opt && rm -rf Python*
