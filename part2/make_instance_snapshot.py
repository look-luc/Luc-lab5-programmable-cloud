from google.cloud import compute_v1


def create_instance(
    project_id: str="lab5-509001",
    zone: str="us-west1-b",
    instance_name: str="part_1_lab5",
    snapshot_name: str="YOUR_SNAPSHOT_NAME"
):
    # Initialize the client
    instance_client = compute_v1.InstancesClient()

    # Define the machine type and source image (Debian 11)
    machine_type = f"zones/{zone}/machineTypes/f1-micro"
    source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
    source_snapshot = f"projects/{project_id}/global/snapshots/{snapshot_name}"

    # Configure the boot disk
    disk = compute_v1.AttachedDisk()
    disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    disk.initialize_params.disk_size_gb = 10
    disk.initialize_params.source_snapshot = source_snapshot
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
                    ports=["5000"]
                )
            ],
            source_ranges=["0.0.0.0/0"],
            target_tags=["allow-5000"]
        )
        print("Creating firewall rule 'allow-5000'...")

        operation = firewall_client.insert(
            project=project_id,
            firewall_resource=firewall_rule
        )

        # Wait for the operation to complete
        operation.result()
        print("Firewall rule successfully created!")

    with open('setup.sh', 'r') as file:
        bash_file = file.read()

    metadata = compute_v1.Metadata(
        items=[
            compute_v1.Items(
                key="startup-script",
                value=bash_file
            )
        ]
    )

    # Combine everything into an Instance object
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = machine_type
    instance.disks = [disk]
    instance.network_interfaces = [network_interface]
    instance.metadata = metadata

    instance = instance_client.get(project=project_id, zone=zone, instance=instance_name)
    current_tags = list(instance.tags.items) if instance.tags.items else []
    current_fingerprint = instance.tags.fingerprint

    updated_tags_list = list(set(current_tags + ["allow-5000"]))

    tags_resource = compute_v1.Tags(
        items=updated_tags_list,
        fingerprint=current_fingerprint
    )

    print(f"Updating tags on '{instance_name}' to: {updated_tags_list}...")
    operation = instance_client.set_tags(
        project=project_id,
        zone=zone,
        instance=instance_name,
        tags_resource=tags_resource
    )
    operation.result()
    print(f"Successfully added tags to VM '{instance_name}'!")

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

    created_instance = instance_client.get(project=project_id, zone=zone, instance=instance_name)
    public_ip = created_instance.network_interfaces[0].access_configs[0].nat_ip

    print(f"\nThe Flask application is available at:\nhttp://{public_ip}:500")
