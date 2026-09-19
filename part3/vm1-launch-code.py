import os

import google.oauth2.service_account as service_account
import googleapiclient.discovery
from google.cloud import compute_v1

KEY_FILE = "/srv/service-credentials.json"

def vm1_launch():
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    project = os.getenv('GOOGLE_CLOUD_PROJECT')
    service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

    zone = "us-west1-b"
    vm2_name = "part-3-flask-app"

    firewall_client = compute_v1.FirewallsClient()
    try:
        firewall_client.get(project=project, firewall="allow-5000")
    except Exception:
        firewall_rule = compute_v1.Firewall(
            name="allow-5000",
            direction="INGRESS",
            priority=1000,
            network="global/networks/default",
            allowed=[
                compute_v1.Allowed(
                    I_p_protocol="tcp",
                    ports=["5000"]
                )
            ],
            source_ranges=["0.0.0.0/0"],
            target_tags=["allow-5000"]
        )
        print("Creating firewall rule 'allow-5000'...")

        operation = firewall_client.insert(
            project=project,
            firewall_resource=firewall_rule
        )

        # Wait for the operation to complete
        operation.result()
        print("Firewall rule successfully created!")

    with open("/srv/vm2-startup-script.sh", 'r') as file:
        vm2_startup = file.read()

    machine_type = f"zones/{zone}/machineTypes/f1-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

    disk = compute_v1.AttachedDisk()
    disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    disk.initialize_params.disk_size_gb = 10
    disk.initialize_params.source_image = source_image
    disk.boot = True
    disk.auto_delete = True

    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "global/networks/default"

    # Adding an empty AccessConfig forces GCP to assign a public Ephemeral IP
    access_config = compute_v1.AccessConfig()
    access_config.name = "External NAT"
    access_config.type_ = "ONE_TO_ONE_NAT"
    network_interface.access_configs = [access_config]

    metadata = [
        {
            "key": "startup-script",
            "value": vm2_startup
        }
    ]

    instance = compute_v1.Instance()
    instance.name = vm2_name
    instance.machine_type = machine_type
    instance.disks = [disk]
    instance.network_interfaces = [network_interface]
    instance.metadata = metadata

    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project
    request.instance_resource = instance

    instance_client = compute_v1.InstancesClient()

    # Trigger the creation process
    print(f"Creating the {vm2_name} instance in {zone}...")
    operation = instance_client.insert(request=request)
    operation.result()

    request = compute_v1.InsertInstanceRequest()
    request.zone = zone
    request.project = project
    request.instance_resource = instance

    # Trigger the creation process
    print(f"Creating the {vm2_name} instance in {zone}...")
    operation = instance_client.insert(request=request)

    # Wait for the operation to complete
    operation.result()
    print(f"Instance {vm2_name} successfully created!")

    created_instance = instance_client.get(
        project=project,
        zone=zone,
        instance=vm2_name
    )
    public_ip = created_instance.network_interfaces[0].access_configs[0].nat_ip

    print(f"\nThe Flask application is available at:\nhttp://{public_ip}:500")
