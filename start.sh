#!/bin/bash

name="server_island"
arkserver_dir="/home/steam/ARK"

saved_dir="${PWD}/${name}/Saved"
cmdline=$(cat ${PWD}/${name}/cmdline)

set -xeuo pipefail

#podman kill --signal INT ${name}

podman run -d --name ${name} \
	-v ${arkserver_dir}:/ARK \
	-v ${saved_dir}:/ARK/ShooterGame/Saved \
	--network host \
	--ulimit nofile=100000 \
	arkserver /ARK/ShooterGame/Binaries/Linux/ShooterGameServer ${cmdline}
