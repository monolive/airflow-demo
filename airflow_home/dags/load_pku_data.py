from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.azure_container_plugin import AzureContainerOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2018, 1, 17),
    'email': ['monoliv@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

dag = DAG('load_pku_data',
    default_args=default_args,
    schedule_interval='*/5 * * * *'
    )

dummy_task = DummyOperator(task_id='dummy_task', dag=dag)


download_file = AzureContainerOperator(
    task_id='download_file_from_azure',
    container_name = 'azure-test',
    container_image = 'sftp-client:v2',
    container_cpu = 1,
    container_mem = 1,
    azure_location = 'westeurope',
    container_volume = [{'name':'config', 'mount_path':'/mnt/conf'}, {'name':'data','mount_path':'/mnt/data'}],
    dag=dag
)

download_file >> dummy_task
