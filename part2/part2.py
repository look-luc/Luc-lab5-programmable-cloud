#!/usr/bin/env python3

import time

import google.auth
import googleapiclient.discovery
from google.cloud import compute_v1
from make_instance_snapshot import create_instance

credentials, project = google.auth.default()
service = googleapiclient.discovery.build("compute", "v1", credentials=credentials)


def create_gcp_snapshot(project_id, disk_name, zone, snapshot_name):
    disk_client = compute_v1.DisksClient()
    snapshot_client = compute_v1.SnapshotsClient()

    disk = disk_client.get(project=project_id, zone=zone, disk=disk_name)

    snapshot_resource = compute_v1.Snapshot(
        name=snapshot_name, source_disk=disk.self_link
    )

    print(f"Creating snapshot '{snapshot_name}' from disk '{disk_name}'...")
    operation = snapshot_client.insert(
        project=project_id, snapshot_resource=snapshot_resource
    )
    operation.result()  # Wait for snapshot creation to complete
    print(f"Snapshot '{snapshot_name}' successfully created!")

    return snapshot_name


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result["items"] if "items" in result else None


if __name__ == "__main__":
    instances = list_instances(service, project, "us-west1-c")
    base_snapshot = None

    if instances:
        first_instance = instances[0]
        instance_name = first_instance["name"]

        # Extract disk name from source URL
        disk_url = first_instance["disks"][0]["source"]
        disk_name = disk_url.split("/")[-1]

        snapshot_name = f"base-snapshot-{instance_name}"
        base_snapshot = create_gcp_snapshot(
            project_id=project,
            disk_name=disk_name,
            zone="us-west1-b",
            snapshot_name=snapshot_name,
        )

    if base_snapshot:
        time_elapsed = {}
        for instance_num in range(3):
            start_time = time.perf_counter()
            new_vm_name = f"part2-instance-{instance_num}"
            print("=" * 20)
            print(f"\nCreating VM instance {instance_num} ({new_vm_name})\n")
            print("=" * 20)

            create_instance(
                project_id=project,
                zone="us-west1-b",
                instance_name=new_vm_name,
                snapshot_name=base_snapshot,
            )

            end_time = time.perf_counter()
            time_elapsed[f"instance_{instance_num}"] = f"{end_time - start_time:.2f} seconds"

        with open("TIMING.md", "w") as file:
            file.write("# Execution Timing\n\n")
            for key, val in time_elapsed.items():
                file.write(f"- **{key}**: {val}\n")
            print("Timing measurements successfully saved to TIMING.md!")
