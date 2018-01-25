import logging
import time

from airflow.exceptions import AirflowException
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

def _create_container_group(client, resource_group_name, name, location, image, memory, cpu, volumes):
    # Start new containers
    # setup default values
    port = 80
    container_resource_requirements = None
    command = None
    environment_variables = None

    if volumes:
        az_volume_mount = []
        az_volumes = []
        for volume in volumes:
            az_volume_mount = az_volume_mount + [VolumeMount(name=str(volume['name']), mount_path=volume['mount_path'])]
            az_file  = AzureFileVolume(
                        share_name=str(volume['name']),
                        storage_account_name=Variable.get("STORAGE_ACCOUNT_NAME"),
                        storage_account_key=Variable.get("STORAGE_ACCOUNT_KEY_PASSWD")
                        )

            az_volumes = az_volumes + [Volume(name=str(volume['name']), azure_file=az_file)]

    # set memory and cpu
    container_resource_requests = ResourceRequests(memory_in_gb = memory, cpu = cpu)
    container_resource_requirements = ResourceRequirements(requests = container_resource_requests)
    container = Container(name = name,
                         image = image,
                         resources = container_resource_requirements,
                         command = command,
                         ports = [ContainerPort(port=port)],
                         environment_variables = environment_variables,
                         volume_mounts = az_volume_mount)

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
                           volumes = az_volumes)

    results = client.container_groups.create_or_update(resource_group_name, name, cgroup)
    return(results)


class AzureContainerOperator(BaseOperator):

    """
    kwargs is perfect for passing storage info
    """
    @apply_defaults
    def __init__(self, container_name, container_image, container_cpu, container_mem, container_volume, azure_location, *args, **kwargs):
        self.container_name = container_name
        self.container_image = container_image
        self.container_cpu = container_cpu
        self.container_mem = container_mem
        self.container_volume = container_volume
        self.azure_location = azure_location
        super(AzureContainerOperator, self).__init__(*args, **kwargs)


    def execute(self, context):
        resource_group_name = self.container_name + "-resource-group"
        image =  Variable.get("CONTAINER_REGISTRY")+ "/" + self.container_image
        self.log.info('Starting image %s', self.container_image)
        resource_client, client = _az_connect()
        resource_client.resource_groups.create_or_update(resource_group_name, { 'location': self.azure_location })
        results = _create_container_group(client, resource_group_name,
                              self.container_name,
                              self.azure_location,
                              image,
                              self.container_mem,
                              self.container_cpu,
                              self.container_volume
                              )

        if results.provisioning_state=='Creating':
            self.log.info('Container started!')
        while True:
            cgroup = client.container_groups.get(resource_group_name, self.container_name)
            for container in cgroup.containers:
                status = container.instance_view.current_state.state
                if  status == 'Terminated':
                    self.log.info('Container is %s', status)
                    logs = client.container_logs.list(resource_group_name, self.container_name, self.container_name)
                    self.log.info(logs.content)
                    break
            time.sleep(5)
        return cgroup.instance_view.state


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
