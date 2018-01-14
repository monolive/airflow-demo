#!/usr/bin/env python

import sys
import ConfigParser
import argparse

from utilities import AzureContext
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, Port, IpAddress,
                                                 ResourceRequirements, ResourceRequests, ContainerGroupNetworkProtocol,
                                                 ContainerGroupRestartPolicy, OperatingSystemTypes, VolumeMount,
                                                 ImageRegistryCredential, AzureFileVolume, Volume)

def main():
    args = parsing_options()
    az_conf = read_az_conf(args.azureConf)
    resource_client, client = connect_azure(az_conf)

    list_container_groups(client)

    resource_group_name = args.name + "-resource-group"
    image = az_conf['CONTAINER_REGISTRY'] + "/" + args.image

    resource_client.resource_groups.create_or_update(resource_group_name, { 'location': az_conf['AZURE_LOCATION'] })

    create_container_group(az_conf, client, resource_group_name = resource_group_name,
                          name = args.name,
                          location = az_conf['AZURE_LOCATION'],
                          image = image,
                          memory = 1,
                          cpu = 1)

    show_container_group(client, resource_group_name, args.name)

    #delete_resources(client, resource_client, resource_group_name, args.name)

def parsing_options():
    # Parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', action='store', dest='name',
                        help='container name (default: %(default)s)',
                        required=False, default='az-test')
    parser.add_argument('-i', '--image-name', action='store', dest='image',
                        help='image name (default: %(default)s)',
                        required=False, default='az-test:v5')
    parser.add_argument('-v', '--volumes', action='store', dest='volumes',
                        help='volume with the format: "name:mount_point"',
                        required=False)
    parser.add_argument('--azure-conf', action='store', dest='azureConf',
                        help='file containing azure credentials (default: %(default)s)',
                        required=False, default='/home/orenault/Developments/airflow-demo/conf/azure.conf')

    return parser.parse_args()


def read_az_conf(azureConfFile):
    # Read Azure configuration file
    azure = {}
    try:
        with open(azureConfFile, 'r') as conf:
            config = ConfigParser.ConfigParser()
            config.readfp(conf)
            for section_name in config.sections():
                for name, value in config.items(section_name):
                    azure[name] = value
        return azure
    except IOError:
        print ("Can't read azure conf file!")

def connect_azure(azure):
    # Connect to Azure
    azure_context = AzureContext(
        subscription_id = azure['azure_subscription_id'],
        client_id = azure['azure_client_id'],
        client_secret = azure['azure_client_secret'],
        tenant = azure['azure_tenant_id']
    )

    # construct the clients
    resource_client = ResourceManagementClient(azure_context.credentials, azure_context.subscription_id)
    client = ContainerInstanceManagementClient(azure_context.credentials, azure_context.subscription_id)
    return resource_client, client

def list_container_groups(client):
    # List known containers
    container_groups = client.container_groups.list()
    for container_group in container_groups:
        print("\t{0}: {{ location: '{1}', containers: {2} }}".format(
            container_group.name,
            container_group.location,
            len(container_group.containers))
        )

def create_container_group(az_conf, client, resource_group_name, name, location, image, memory, cpu):
    # Start new containers
    # setup default values
    port = 80
    container_resource_requirements = None
    command = None
    environment_variables = None
    volume_mount = [VolumeMount(name='config', mount_path='/mnt/config'),VolumeMount(name='data', mount_path='/mnt/data')]
    # data_volume_mount = [VolumeMount(name='data', mount_path='/mnt/data')]

    # set memory and cpu
    container_resource_requests = ResourceRequests(memory_in_gb = memory, cpu = cpu)
    container_resource_requirements = ResourceRequirements(requests = container_resource_requests)

    az_config_file_volume = AzureFileVolume(share_name='config',
                            storage_account_name=az_conf['storage_account_name'],
                            storage_account_key=az_conf['storage_account_key'])
    az_data_file_volume = AzureFileVolume(share_name='data',
                            storage_account_name=az_conf['storage_account_name'],
                            storage_account_key=az_conf['storage_account_key'])


    #volume_mount = VolumeMount(name='config', mount_path='/mnt/config')
    volumes = [Volume(name='config', azure_file=az_config_file_volume),Volume(name='data', azure_file=az_data_file_volume)]
    container = Container(name = name,
                         image = image,
                         resources = container_resource_requirements,
                         command = command,
                         ports = [ContainerPort(port=port)],
                         environment_variables = environment_variables,
                         volume_mounts = volume_mount)

    # defaults for container group
    cgroup_os_type = OperatingSystemTypes.linux
    cgroup_restart_policy = ContainerGroupRestartPolicy.never

    image_registry_credential = ImageRegistryCredential(server=az_conf['container_registry'],
                                                        username=az_conf['container_registry_user'],
                                                        password=az_conf['container_registry_pwd'])

    cgroup = ContainerGroup(location = location,
                           containers = [container],
                           os_type = cgroup_os_type,
                           image_registry_credentials = [image_registry_credential],
                           restart_policy = cgroup_restart_policy,
                           volumes = volumes)

    client.container_groups.create_or_update(resource_group_name, name, cgroup)

def show_container_group(client, resource_group_name, name):
    cgroup = client.container_groups.get(resource_group_name, name)

    print('\n{0}\t\t\t{1}\t{2}'.format('name', 'location', 'provisioning state'))
    print('---------------------------------------------------')
    print('{0}\t\t{1}\t\t{2}'.format(cgroup.name, cgroup.location, cgroup.provisioning_state))

def delete_resources(client, resource_client, resource_group_name, container_group_name):
    client.container_groups.delete(resource_group_name, container_group_name)
    resource_client.resource_groups.delete(resource_group_name)

if __name__ == "__main__":
    main()
