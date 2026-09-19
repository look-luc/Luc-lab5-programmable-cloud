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
credentials = service_account.Credentials.from_service_account_file(filename='service-credentials.json')
project = os.getenv('GOOGLE_CLOUD_PROJECT') or 'FILL IN YOUR PROJECT'
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def lauch_vm1(
    project_id:str,
    zone:str,
    vm1_name:str,
    vm1_bash_name:str,
    vm2_bash_name:str,
    vm2_bash_name_setup:str,
    key_path:str="part3/lab5-509001-3545ed9a8ef5.json"
):
    machine_type = f"zones/{zone}/machineTypes/f1-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

    with open(vm1_bash_name, 'r') as file:
        bash_file_vm1 = file.read()

    with open(vm2_bash_name, 'r') as file:
        bash_file_vm2 = file.read()

    with open(vm2_bash_name_setup, 'r') as file:
        setup_vm2 = file.read()

    with open(key_path, 'r') as file:
        service_key = file.read()

    vm1_metadata = [
        {"key": "startup-script", "value": bash_file_vm1},
        {"key": "vm1-launch-vm2-code", "value": bash_file_vm2},
        {"key": "service-credentials", "value": service_key},
        {"key": "vm2-startup-script", "value": setup_vm2},
        {"key": "project", "value": project_id}
    ]

    vm_instance_1 = compute_v1.Instance()
    vm_instance_1.name = vm1_name
    vm_instance_1.machine_type = machine_type
    vm_instance_1.metadata = vm1_metadata
    vm_instance_1.source = source_image

    instance_client = compute_v1.InstancesClient()
    instance = instance_client.get(
        project=project_id,
        zone=zone,
        instance=vm1_name
    )
    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project_id
    request.instance_resource = instance

    # Trigger the creation process
    print(f"Creating the {vm1_name} instance in {zone}...")
    operation = instance_client.insert(request=request)

    # Wait for the operation to complete
    operation.result()
    print(f"Instance {vm1_name} successfully created!")

if __name__ == "__main__":
    print("Your running instances are:")
    for instance in list_instances(service, project, 'us-west1-b'):
        print(instance['name'])
