#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import google.auth
import googleapiclient.discovery
import vm_app

credentials, project = vm_app.get_adc_credentials()
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

if __name__ == "__main__":
    vm_app.create_instance()

    print("Your running instances are:")
    for instance in list_instances(service, project, 'us-west1-b'):
        print(instance['name'])
