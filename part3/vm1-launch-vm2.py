#!/usr/bin/env python3

import os

import google.oauth2.service_account as service_account
from google.cloud import compute_v1

# Load explicit service account credentials saved from metadata
credentials = service_account.Credentials.from_service_account_file('service-credentials.json')
project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or 'lab5-509001'
zone = 'us-west1-a'
vm2_name = 'vm2-flask-app'

instance_client = compute_v1.InstancesClient(credentials=credentials)
firewall_client = compute_v1.FirewallsClient(credentials=credentials)

# Check or create firewall rule allow-5000
try:
    firewall_client.get(project=project_id, firewall="allow-5000")
except Exception:
    firewall_rule = compute_v1.Firewall(
        name="allow-5000",
        direction="INGRESS",
        priority=1000,
        network="global/networks/default",
        allowed=[compute_v1.Allowed(I_p_protocol="tcp", ports=["5000"])],
        source_ranges=["0.0.0.0/0"],
        target_tags=["allow-5000"]
    )
    op = firewall_client.insert(project=project_id, firewall_resource=firewall_rule)
    op.result()

# Disk config
disk = compute_v1.AttachedDisk()
disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
disk.initialize_params.disk_size_gb = 10
disk.initialize_params.source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
disk.boot = True
disk.auto_delete = True

# Network config
network_interface = compute_v1.NetworkInterface()
network_interface.name = "global/networks/default"
access_config = compute_v1.AccessConfig()
access_config.name = "External NAT"
access_config.type_ = "ONE_TO_ONE_NAT"
network_interface.access_configs = [access_config]

# Load VM2 setup script
with open('vm2-startup-script.sh', 'r') as f:
    vm2_startup = f.read()

metadata = compute_v1.Metadata(
    items=[compute_v1.Items(key="startup-script", value=vm2_startup)]
)

tags = compute_v1.Tags(items=["allow-5000"])

instance = compute_v1.Instance()
instance.name = vm2_name
instance.machine_type = f"zones/{zone}/machineTypes/f1-micro"
instance.disks = [disk]
instance.network_interfaces = [network_interface]
instance.metadata = metadata
instance.tags = tags

request = compute_v1.InsertInstanceRequest(
    project=project_id,
    zone=zone,
    instance_resource=instance
)

print(f"VM 1 is launching {vm2_name}...")
operation = instance_client.insert(request=request)
operation.result()
print(f"VM 2 ({vm2_name}) successfully launched!")

created_instance = instance_client.get(project=project_id, zone=zone, instance=vm2_name)
public_ip = created_instance.network_interfaces[0].access_configs[0].nat_ip
print(f"\nThe Flask application is available at:\nhttp://{public_ip}:5000")
