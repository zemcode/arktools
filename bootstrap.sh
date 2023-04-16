#!/bin/bash

set -xeuo pipefail

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
