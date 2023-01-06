#!/bin/sh
apt update && apt upgrade -y
#apt autoclean
#apt clean
#apt autoremove -y

# Mosquitto
apt install mosquitto mosquitto-clients
echo "listener 1883">>/etc/mosquitto/mosquitto.conf
echo "allow_anonymous true">>/etc/mosquitto/mosquitto.conf

# Depends
apt install -y python3 python3-dev python3-pip
apt install -y libavahi-compat-libdnssd-dev # HomeKit
apt install -y bluez libffi-dev libssl-dev libjpeg-dev zlib1g-dev autoconf build-essential libopenjp2-7 libtiff5 libturbojpeg0-dev tzdata

# PIP
cat <<EOF > ~/.pip/pip.conf
[global]
index-url = http://mirrors.aliyun.com/pypi/simple/
[install]
trusted-host = http://mirrors.aliyun.com
EOF

# Hass
pip3 install homeassistant -i http://mirrors.aliyun.com/pypi/simple/

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
