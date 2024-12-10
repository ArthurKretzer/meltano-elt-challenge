from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
import os

PROJECT_ROOT = os.getenv("MELTANO_PROJECT_ROOT", os.getcwd())
MELTANO_BIN = ".meltano/run/bin"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=10),
}

dag = DAG(
    "ELT_with_meltano",
    schedule_interval="@daily",
    start_date=datetime(2024, 12, 1),
    max_active_runs=1,
    catchup=True,
    render_template_as_native_obj=True,
)

extract_csv = BashOperator(
    task_id="extract_csv_to_csv",
    bash_command=(
        f"cd {PROJECT_ROOT}; "
        "MELTANO_ENVIRONMENT=extract "
        "SOURCE=csv "
        "DATESTAMP={{ dag_run.conf['custom_elt_date'] | default(ds) }} "
        f"{MELTANO_BIN} run tap-csv target-csv"
    ),
    dag=dag,
)

extract_postgres = BashOperator(
    task_id="extract_postgres_to_csv",
    bash_command=(
        f"cd {PROJECT_ROOT}; "
        "MELTANO_ENVIRONMENT=extract "
        "SOURCE=postgres "
        "DATESTAMP={{ dag_run.conf['custom_elt_date'] | default(ds) }} "
        f"{MELTANO_BIN} run tap-postgres target-csv"
    ),
    dag=dag,
)

load_to_postgres = BashOperator(
    task_id="load_csv_data_to_postgres",
    bash_command=(
        f"cd {PROJECT_ROOT}; "
        "MELTANO_ENVIRONMENT=load "
        "SCHEMA=public "
        "EXTRACTED_AT={{ dag_run.conf['custom_elt_date'] | default(ds) }} "
        f"{MELTANO_BIN} run tap-csv target-postgres"
    ),
    dag=dag,
)

[extract_csv, extract_postgres] >> load_to_postgres
