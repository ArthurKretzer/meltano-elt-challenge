from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

# Define o DAG
dag = DAG(
    "ELT_with_meltano",
    schedule_interval="0 0 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
)


def extract_csv_to_csv():
    import os

    env_vars = "SOURCE=csv TIMESTAMP=$(date +%Y-%m-%d)"
    env_vars += " CSV_FILE_DEFINITION=./extract/extract_csv_files_definition.json"
    meltano_command = "meltano schedule run daily-csv-load"
    os.system(env_vars + meltano_command)


extract_csv = PythonOperator(
    task_id="extract_csv_to_csv",
    python_callable=extract_csv_to_csv,
    dag=dag,
)


def extract_postgres_to_csv():
    import os

    env_vars = "SOURCE=postgres TIMESTAMP=$(date +%Y-%m-%d)"
    meltano_command = "meltano run tap-postgres target-csv"
    os.system(env_vars + meltano_command)


extract_postgres = PythonOperator(
    task_id="extract_postgres_to_csv",
    python_callable=extract_postgres_to_csv,
    dag=dag,
)


def load_csv_data_to_postgres():
    import os

    env_vars = (
        "SCHEMA=public CSV_FILE_DEFINITION=./extract/load_csv_files_definition.json"
    )
    env_vars += " EXTRACTED_AT=$(date +%Y-%m-%d)"
    meltano_command = "meltano run tap-csv target-postgres"
    os.system(env_vars + meltano_command)


load_to_postgres = PythonOperator(
    task_id="load_csv_data_to_postgres",
    python_callable=load_csv_data_to_postgres,
    dag=dag,
)

[extract_csv, extract_postgres] >> load_to_postgres
