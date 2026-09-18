import subprocess

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import compute_v1


def get_adc_credentials():
    try:
        credentials, project = google.auth.default()
        return credentials, project
    except DefaultCredentialsError:
        print("ADC credentials not found. Triggering gcloud login...")
        subprocess.run(["gcloud", "auth", "application-default", "login"], check=True)
        return google.auth.default()

def create_instance(
    project_id: str="lab5-509001",
    zone: str="us-west1-b",
    instance_name: str="part_1_lab5"
):
    # Initialize the client
    instance_client = compute_v1.InstancesClient()

    # Define the machine type and source image (Debian 11)
    machine_type = f"zones/{zone}/machineTypes/f1-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

    # Configure the boot disk
    disk = compute_v1.AttachedDisk()
    disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    disk.initialize_params.disk_size_gb = 10
    disk.initialize_params.source_image = source_image
    disk.boot = True
    disk.auto_delete = True  # Delete the disk when the VM is deleted

    # Configure the network interface (assigns an external IP address)
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "global/networks/default"

    # Adding an empty AccessConfig forces GCP to assign a public Ephemeral IP
    access_config = compute_v1.AccessConfig()
    access_config.name = "External NAT"
    access_config.type_ = "ONE_TO_ONE_NAT"
    network_interface.access_configs = [access_config]

    # Combine everything into an Instance object
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = machine_type
    instance.disks = [disk]
    instance.network_interfaces = [network_interface]

    # Prepare the request
    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project_id
    request.instance_resource = instance

    # Trigger the creation process
    print(f"Creating the {instance_name} instance in {zone}...")
    operation = instance_client.insert(request=request)

    # Wait for the operation to complete
    operation.result()
    print(f"Instance {instance_name} successfully created!")
