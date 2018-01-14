#!/usr/bin/env python
import argparse
import sys
import ConfigParser

from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings

def main():
    args = parsing_options()
    az_conf = read_az_conf(args.azureConf)
    block_blob_service = BlockBlobService(account_name=az_conf['storage_account_name'], account_key=az_conf['storage_account_key'])
    block_blob_service.create_container('mycontainer')
    block_blob_service.create_blob_from_path(
        'mycontainer',
        'test.zip',
        '/tmp/test.zip',
        content_settings=ContentSettings(content_type='application/zip',content_md5='M2E5OTI1N2ZmMTRiNDExNzk1ZmFiMDEyZjQ3OGQ3ODIKi')
        )
    generator = block_blob_service.list_blobs('mycontainer')
    for blob in generator:
        print blob.name
        print blob.properties
        print blob.metadata


def parsing_options():
    # Parse command line options
    parser = argparse.ArgumentParser()
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


if __name__ == "__main__":
    main()
