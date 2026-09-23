#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import google.auth
import google.oauth2.service_account as service_account
import googleapiclient.discovery
from google.cloud import compute_v1

#
# Use Google Service Account - See https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.service_account.html#module-google.oauth2.service_account
#
KEY_PATH = "part3/lab5-509001-dc1e1e9a4cd7.json"
credentials = service_account.Credentials.from_service_account_file(filename=KEY_PATH)
project = os.getenv('GOOGLE_CLOUD_PROJECT') or 'lab5-509001'
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def launch_vm1(
    project_id: str,
    zone: str,
    vm1_name: str,
    vm1_bash_name: str,
    vm2_bash_name: str,
    vm2_bash_name_setup: str,
    key_path: str = KEY_PATH
):
    machine_type = f"zones/{zone}/machineTypes/f1-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

    with open(vm1_bash_name, 'r') as f:
        bash_file_vm1 = f.read()

    with open(vm2_bash_name, 'r') as f:
        bash_file_vm2 = f.read()

    with open(vm2_bash_name_setup, 'r') as f:
        setup_vm2 = f.read()

    with open(key_path, 'r') as f:
        service_key = f.read()

    metadata_items = [
        compute_v1.Items(key="startup-script", value=bash_file_vm1),
        compute_v1.Items(key="vm1-launch-vm2-code", value=bash_file_vm2),
        compute_v1.Items(key="service-credentials", value=service_key),
        compute_v1.Items(key="vm2-startup-script", value=setup_vm2),
        compute_v1.Items(key="project", value=project_id)
    ]
    metadata = compute_v1.Metadata(items=metadata_items)

    disk = compute_v1.AttachedDisk()
    disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    disk.initialize_params.disk_size_gb = 10
    disk.initialize_params.source_image = source_image
    disk.boot = True
    disk.auto_delete = True

    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "global/networks/default"
    access_config = compute_v1.AccessConfig()
    access_config.name = "External NAT"
    access_config.type_ = "ONE_TO_ONE_NAT"
    network_interface.access_configs = [access_config]

    vm_instance_1 = compute_v1.Instance()
    vm_instance_1.name = vm1_name
    vm_instance_1.machine_type = machine_type
    vm_instance_1.disks = [disk]
    vm_instance_1.network_interfaces = [network_interface]
    vm_instance_1.metadata = metadata

    instance_client = compute_v1.InstancesClient(credentials=credentials)

    request = compute_v1.InsertInstanceRequest(
        project=project_id,
        zone=zone,
        instance_resource=vm_instance_1
    )

    print(f"Creating launcher VM ({vm1_name}) in {zone}...")
    operation = instance_client.insert(request=request)
    operation.result()
    print(f"Instance {vm1_name} successfully created!")


if __name__ == "__main__":
    launch_vm1(
        project_id=project,
        zone="us-west1-a",
        vm1_name="vm1-launcher",
        vm1_bash_name="setup_vm1.sh",
        vm2_bash_name="vm1_launch_vm2.py",
        vm2_bash_name_setup="setup.sh"
    )

    print("\nYour running instances are:")
    for instance in list_instances(service, project, 'us-west1-a'):
        print(instance['name'])
