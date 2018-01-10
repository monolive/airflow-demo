# airflow-demo
Airflow process to load PKU data

- How to install python Requirements
```
virtualenv venv-azure
source venv-azure/bin/activate
pip install -r requirements.txt
```

- How to create Container
```
# https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli

# build the image with
docker build -t az-test -f Dockerfile .  

# tag the container against your Azure docker registry
docker tag az-test monolivedockerregistry.azurecr.io/az-test:v4

# Push to Azure docker registry
az acr login --name monolivedockerregistry

# If you are getting a permission denied when pushing
# Log to azure
az login

# Log to your Azure Private registry
az acr login --name monolivedockerregistry
```
- Create config file
```
[Azure]
AZURE_SUBSCRIPTION_ID = 
AZURE_TENANT_ID =
AZURE_CLIENT_ID =
AZURE_CLIENT_SECRET =
AZURE_LOCATION =

[Container]
CONTAINER_REGISTRY =
CONTAINER_REGISTRY_USER =
CONTAINER_REGISTRY_PWD =

[Volume]
STORAGE_ACCOUNT_NAME =
STORAGE_ACCOUNT_KEY =
```
