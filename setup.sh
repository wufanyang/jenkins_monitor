#!/bin/bash
# Run this script as root to setup a centos machine.
# After running this script, Jenkins server is running
# in a docker container.
# A cron job is setup to monitor jenkins server health.
# Please note that you should only run this script in a clean centos only once.

# exit on errors
set -e

# add perforce repo for installing helix-cli
cat >> /etc/yum.repos.d/perforce.repo <<EOF
[perforce]
name=Perforce
baseurl=http://package.perforce.com/yum/rhel/7/x86_64
enabled=1
gpgcheck=1
gpgkey=http://package.perforce.com/perforce.pubkey
EOF

# install P4
yum install -y helix-cli

# setup perforce environment
mkdir /home/perforce/
chmod -R a+rw /home/perforce/

cat >> /home/perforce/.p4config <<EOF
P4USER=nishbuild
P4CLIENT=nishbuild-ori-seq-linux
P4PORT=perforce.natinst.com:1666
EOF

cat >> ~/.p4tickets <<EOF
localhost:perforce_cluster=nishbuild:089BE530E12B8E790D97E62D00E200DD
EOF

# install pip
yum install -y epel-release
yum install -y python-pip

# install patch for p4pythonic
yum install -y gcc-c++ python-devel openssl-devel

# install docker
yum install -y yum-utils \
  device-mapper-persistent-data \
  lvm2
yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce
systemctl start docker
systemctl enable docker

# install docker compose
curl -L https://github.com/docker/compose/releases/download/1.17.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
# verify docker-compose is installed successfully
docker-compose --version

# setup perforce workspace
cd /home/perforce/
export P4CONFIG=/home/perforce/.p4config
p4 client -o | p4 client -i

# TODO: we use source code in p4, so we need to hard code path here.
# We may make source code into a python package in the future,
# and use pip install, so that we don't need to hard code path here.
p4_path=//IndustrialComm/Group/phoebe/jenkins_monitor/2.0
p4 sync -f $p4_path/...
p4_where=($(p4 where $p4_path))
local_path=${p4_where[2]}
cd $local_path

# install dependencies
pip install -r dependencies -i http://ori-pypi.ni.corp.natinst.com/simple --trusted-host ori-pypi.ni.corp.natinst.com
# sync docker files to local, build image and start container
python main.py --check_p4

# create health check as cron job
crontab -l | { cat; echo "*/10 * * * * python $local_path/main.py --check_health"; } | crontab -
systemctl start crond

