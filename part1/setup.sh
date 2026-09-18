#!/bin/bash

VM_NAME=$1
VM_ZONE=$2

sudo apt-get update
sudo apt-get install -y python3 python3-pip git
sudo pip3 install google-cloud-compute
git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial
cd flask-tutorial
sudo python3 setup.py install
sudo pip3 install -e .

export FLASK_APP=flaskr
flask init-db
nohup flask run -h 0.0.0.0 &

cd ..

gcloud compute firewall-rules create allow-tcp-5000 \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:5000 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=allow-5000

gcloud compute instances add-tags "$VM_NAME"\
    --tags=allow-5000\
    --zone="$VM_ZONE"

git clone https://github.com/GoogleCloudPlatform/python-docs-samples.git
