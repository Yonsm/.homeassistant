#!/bin/sh

cat <<\EOF >> ~/.profile
alias mqttsub='mqttsub() { mosquitto_sub -v -t "$1#"; }; mqttsub'
alias dockre='dockre() { cat /dev/null > `docker inspect -f "{{json .LogPath}}" $1 | tr -d \"`; docker restart $1; }; dockre'
alias docksh='docksh() { docker exec -it $1 /bin/bash; }; docksh'
alias docklog='docker logs -f'
alias hasssh='docksh homeassistant'
alias hassre='dockre homeassistant'
alias hasslog="docklog homeassistant"
alias hassrl='hassre; hasslog'
EOF

# Docker
docker run -d --name=homeassistant --privileged --restart=unless-stopped -e TZ=Asia/Shanghai -v /opt/.homeassistant:/config --network=host ghcr.nju.edu.cn/home-assistant/home-assistant:stable
