#!/bin/sh
# Install Home Assistant on OpenWrt

# BASE
opkg install python3 python3-pip
opkg install python3-dev gcc
opkg install python3-cffi # N1 Only
source /usr/bin/gcc_env.sh

# PIP
sed -i '/index-url/d' /etc/pip.conf
echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple/" >> /etc/pip.conf
pip install --upgrade pip

# PIP SO Fix
cat <<\EOF > /usr/bin/pip3sofix
#!/bin/sh
FILE="${1##*/}"
ln -s "$FILE" "${1%/*}/${FILE%%.*}.so"
EOF
cat <<\EOF > /usr/bin/pip3fix
#!/bin/sh
cd /usr/lib/python3.10/site-packages && find . -name "*cpython-*.so" -exec pip3sofix {} \;
cd /root/.homeassistant/deps/lib/python3.10/site-packages && find . -name "*cpython-*.so" -exec pip3sofix {} \;
EOF
chmod +x /usr/bin/pip*fix

# HASS
pip install tzdata homeassistant

# Fix
rm -rf /root/.homeassistant/deps/lib/python3.10/site-packages/zeroconf*
pip3fix
hass
pip3fix
hass -v

# Launch
sed -i '/exit 0/d' /etc/rc.local
echo -e 'hass -c /root/.homeassistant > dev/null &\nexit 0' >> /etc/rc.local

# MQTT
opkg install mosquitto-nossl
cat << \EOF > /etc/mosquitto/mosquitto.conf
listener 1883
allow_anonymous true
allow_zero_length_clientid true
EOF

# MISC
opkg install ffmpeg #adb ...
