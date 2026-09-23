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
    project_id: str = "lab5-509001",
    zone: str = "us-west1-b",
    instance_name: str = "part-1-lab5",
):
    instance_client = compute_v1.InstancesClient()

    machine_type = f"zones/{zone}/machineTypes/e2-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

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

    firewall_client = compute_v1.FirewallsClient()
    try:
        firewall_client.get(project=project_id, firewall="allow-5000")
    except Exception:
        firewall_rule = compute_v1.Firewall(
            name="allow-5000",
            direction="INGRESS",
            priority=1000,
            network="global/networks/default",
            allowed=[
                compute_v1.Allowed(
                    I_p_protocol="tcp",
                    ports=["5000"],
                )
            ],
            source_ranges=["0.0.0.0/0"],
            target_tags=["allow-5000"],
        )
        print("Creating firewall rule 'allow-5000'...")

        operation = firewall_client.insert(
            project=project_id,
            firewall_resource=firewall_rule,
        )

        operation.result()
        print("Firewall rule successfully created!")

    with open("./part1/setup.sh", "r") as file:
        bash_file = file.read()

    metadata = compute_v1.Metadata(
        items=[
            compute_v1.Items(
                key="startup-script",
                value=bash_file,
            )
        ]
    )

    tags = compute_v1.Tags(items=["allow-5000"])

    # Combine everything into an Instance object
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = machine_type
    instance.disks = [disk]
    instance.network_interfaces = [network_interface]
    instance.metadata = metadata
    instance.tags = tags

    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project_id
    request.instance_resource = instance

    print(f"Creating the {instance_name} instance in {zone}...")
    operation = instance_client.insert(request=request)

    operation.result()
    print(f"Instance {instance_name} successfully created!")

    created_instance = instance_client.get(
        project=project_id, zone=zone, instance=instance_name
    )
    public_ip = created_instance.network_interfaces[0].access_configs[0].nat_ip

    print(f"\nThe Flask application is available at:\nhttp://{public_ip}:5000")
