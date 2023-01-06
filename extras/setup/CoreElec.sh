#!/bin/sh

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
