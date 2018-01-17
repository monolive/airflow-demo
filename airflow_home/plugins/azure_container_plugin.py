import logging

from airflow.models import (BaseOperator, Variable)
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults

from utilities import AzureContext
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, Port, IpAddress,
                                                 ResourceRequirements, ResourceRequests, ContainerGroupNetworkProtocol,
                                                 ContainerGroupRestartPolicy, OperatingSystemTypes, VolumeMount,
                                                 ImageRegistryCredential, AzureFileVolume, Volume)


log = logging.getLogger(__name__)

def _az_connect():
    azure_context = AzureContext(
        subscription_id = Variable.get("AZURE_SUBSCRIPTION_ID"),
        client_id = Variable.get("AZURE_CLIENT_ID"),
        client_secret = Variable.get("AZURE_CLIENT_SECRET"),
        tenant = Variable.get("AZURE_TENANT_ID")
    )

    # construct the clients
    resource_client = ResourceManagementClient(azure_context.credentials, azure_context.subscription_id)
    client = ContainerInstanceManagementClient(azure_context.credentials, azure_context.subscription_id)
    return resource_client, client

def _create_container_group(client, resource_group_name, name, location, image, memory, cpu):
    # Start new containers
    # setup default values
    port = 80
    container_resource_requirements = None
    command = None
    environment_variables = None
    volume_mount = [VolumeMount(name='config', mount_path='/mnt/conf'),VolumeMount(name='data', mount_path='/mnt/data')]

    # set memory and cpu
    container_resource_requests = ResourceRequests(memory_in_gb = memory, cpu = cpu)
    container_resource_requirements = ResourceRequirements(requests = container_resource_requests)

    az_config_file_volume = AzureFileVolume(share_name='config',
                            storage_account_name=Variable.get("STORAGE_ACCOUNT_NAME"),
                            storage_account_key=Variable.get("STORAGE_ACCOUNT_KEY_PASSWD"))
    az_data_file_volume = AzureFileVolume(share_name='data',
                            storage_account_name=Variable.get("STORAGE_ACCOUNT_NAME"),
                            storage_account_key=Variable.get("STORAGE_ACCOUNT_KEY_PASSWD"))


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
    image_registry_credential = ImageRegistryCredential(server=Variable.get("CONTAINER_REGISTRY"),
                                                        username=Variable.get("CONTAINER_REGISTRY_USER"),
                                                        password=Variable.get("CONTAINER_REGISTRY_PASSWD")
                                                        )

    cgroup = ContainerGroup(location = location,
                           containers = [container],
                           os_type = cgroup_os_type,
                           image_registry_credentials = [image_registry_credential],
                           restart_policy = cgroup_restart_policy,
                           volumes = volumes)

    client.container_groups.create_or_update(resource_group_name, name, cgroup)


class AzureContainerOperator(BaseOperator):

    """
    kwargs is perfect for passing storage info
    """
    @apply_defaults
    def __init__(self, container_name, container_image, container_cpu, container_mem, azure_location, *args, **kwargs):
        self.container_name = container_name
        self.container_image = container_image
        self.container_cpu = container_cpu
        self.container_mem = container_mem
        self.azure_location = azure_location
        super(AzureContainerOperator, self).__init__(*args, **kwargs)


    def execute(self, context):
        resource_group_name = self.container_name + "-resource-group"
        image =  Variable.get("CONTAINER_REGISTRY")+ "/" + self.container_image
        resource_client, client = _az_connect()
        resource_client.resource_groups.create_or_update(resource_group_name, { 'location': 'westeurope' })
        _create_container_group(client, resource_group_name,
                              self.container_name,
                              'westeurope',
                              image,
                              self.container_mem,
                              self.container_cpu)

        log.info("Hello World!")
        #log.info('operator_param: %s', self.operator_param)


class AzureContainerPlugin(AirflowPlugin):
    name = "azure_container_plugin"
    operators = [AzureContainerOperator]
     # A list of class(es) derived from BaseHook
    hooks = []
    # A list of class(es) derived from BaseExecutor
    executors = []
    # A list of references to inject into the macros namespace
    macros = []
    # A list of objects created from a class derived
    # from flask_admin.BaseView
    admin_views = []
    # A list of Blueprint object created from flask.Blueprint
    flask_blueprints = []
    # A list of menu links (flask_admin.base.MenuLink)
    menu_links = []
