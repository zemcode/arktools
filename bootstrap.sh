#!/bin/bash

set -xeuo pipefail

sudo setenfoce 0

sudo firewall-cmd --add-port=27015/udp --permanent
sudo firewall-cmd --add-port=7777/udp --permanent
sudo firewall-cmd --add-port=7778/udp --permanent
sudo firewall-cmd --add-port=27020/tcp --permanent
sudo firewall-cmd --complete-reload

sudo swapoff /swapfile
sudo fallocate -l 64G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

sudo yum install -y glibc.i686 libstdc++.i686

mkdir -p ${HOME}/steamcmd
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar -C ${HOME}/steamcmd -zxvf -

${HOME}/steamcmd/steamcmd.sh +force_install_dir ${HOME}/ARK +login anonymous +app_update 376030 validate +quit

podman build --tag arkserver ./docker

# 1999447172 Super Structures
# 1609138312 Dino Storage v2
# 1231538641 ARKomatic
# 1404697612 Awesome SpyGlass!
# 889745138  Awesome Teleporters!
# 1315534671 Automatic Death Recovery
# 2182894352 Custom Dino Levels
# 1549436130 Suicide Potion
# 1551199162 Chat Evolved
# 2198615778 MX-E Shopsystem
# 849985437  HG Stacking Mod 5000-90 V316 [Open Source]

./arkmod.py \
  1999447172 \
  1609138312 \
  1231538641 \
  1404697612 \
  889745138  \
  1315534671 \
  2182894352 \
  1549436130 \
  1551199162 \
  2198615778 \
  849985437
