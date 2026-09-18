#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import google.auth
import googleapiclient.discovery
from google.cloud import compute_v1
from make_instance_snapshot import create_instance

credentials, project = google.auth.default()
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

def create_gcp_snapshot(project_id, disk_name, zone, snapshot_name):
    # Initialize the disks and snapshots clients
    disk_client = compute_v1.DisksClient()
    snapshot_client = compute_v1.SnapshotsClient()

    # Get the disk resource
    disk = disk_client.get(project=project_id, zone=zone, disk=disk_name)

    # Define snapshot properties
    snapshot_resource = compute_v1.Snapshot(
        name=snapshot_name,
        source_disk=disk.self_link
    )

    # Trigger snapshot creation
    operation = snapshot_client.insert(
        project=project_id,
        snapshot_resource=snapshot_resource
    )

    print(f"Snapshot creation started. Operation: {operation.name}")

#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

if __name__ == "__main__":
    print("Your running instances are:")
    base_snapshot = ""
    for instance in list_instances(service, project, 'us-west1-b'):
        base_snapshot = create_gcp_snapshot(
            project_id=project,
            disk_name=instance.disks,
            zone="us-west1-b",
            snapshot_name=f"base-snapshot-{instance["name"]}"
        )
        print(instance['name'])

    time_elapsed = {}
    for instance_num in range(3):
        start_time = time.perf_counter()
        print("="*20)
        print(f"\nmaking snapshot instance number {instance_num}\n")
        print("="*20)
        create_instance(snapshot_name=base_snapshot)
        end_time = time.perf_counter()
        time_elapsed[f"{instance_num} instance": end_time-start_time]

    with open("TIMING.md", "w") as file:
        file.write(f"Time elapsed for all three: {time_elapsed}")
