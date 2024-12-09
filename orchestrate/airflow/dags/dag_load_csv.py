from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator

# Define o DAG
dag = DAG(
    "ELT_with_meltano",
    schedule_interval="@daily",
    start_date=datetime(2024, 12, 7),
    catchup=True,
)


def get_execution_date(**kwargs):
    custom_elt_date = Variable.get("custom_elt_date", default_var=None)

    if custom_elt_date:
        print(f"Usando a data definida na variável do Airflow: {custom_elt_date}")
        date = custom_elt_date
    else:
        execution_date = kwargs["execution_date"]
        print(f"Usando a data de execução da DAG: {execution_date}")
        date = execution_date.strftime("%Y-%m-%d")

    return date


def extract_csv_to_csv(**kwargs):
    import os

    date = get_execution_date(kwargs)

    env_vars = "MELTANO_ENVIRONMENT=extract"
    env_vars += f"SOURCE=csv TIMESTAMP={date}"
    env_vars += " CSV_FILE_DEFINITION=./extract/extract_csv_files_definition.json"
    meltano_command = "meltano schedule run tap-csv target-csv"
    os.system(env_vars + meltano_command)


extract_csv = PythonOperator(
    task_id="extract_csv_to_csv",
    python_callable=extract_csv_to_csv,
    dag=dag,
    provide_context=True,
)


def extract_postgres_to_csv(**kwargs):
    import os

    date = get_execution_date(kwargs)

    env_vars = "MELTANO_ENVIRONMENT=extract"
    env_vars += f"SOURCE=postgres TIMESTAMP={date}"
    meltano_command = "meltano run tap-postgres target-csv"
    os.system(env_vars + meltano_command)


extract_postgres = PythonOperator(
    task_id="extract_postgres_to_csv",
    python_callable=extract_postgres_to_csv,
    dag=dag,
    provide_context=True,
)


def load_csv_data_to_postgres(**kwargs):
    import os

    date = get_execution_date(kwargs)

    env_vars = "MELTANO_ENVIRONMENT=load"
    env_vars += (
        "SCHEMA=public CSV_FILE_DEFINITION=./extract/load_csv_files_definition.json"
    )
    env_vars += f"EXTRACTED_AT={date}"
    meltano_command = "meltano run tap-csv target-postgres"
    os.system(env_vars + meltano_command)


load_to_postgres = PythonOperator(
    task_id="load_csv_data_to_postgres",
    python_callable=load_csv_data_to_postgres,
    dag=dag,
    provide_context=True,
)

[extract_csv, extract_postgres] >> load_to_postgres
