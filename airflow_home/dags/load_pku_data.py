from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
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

dag = DAG('LoadPKUData', default_args=default_args)

t1 = BashOperator(
    task_id='grab_data_from_sftp_server',
    bash_command='',
    dag=dag
)

t2 = BashOperator(
    task_id='decrypt_PKU_data',
    bash_command='',
    dag=dag
)

t3 = BashOperator(
    task_id='tmp',
    bash_command='',
    dag=dag
)
