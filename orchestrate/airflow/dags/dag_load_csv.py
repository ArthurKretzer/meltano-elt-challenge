import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Define the root directory for the Meltano project.
# Use the environment variable MELTANO_PROJECT_ROOT if set,
#  otherwise use the current working directory.
PROJECT_ROOT = os.getenv("MELTANO_PROJECT_ROOT", os.getcwd())
# Define the path to the Meltano binary for running tasks.
MELTANO_BIN = ".meltano/run/bin"

# Default arguments for the DAG,
#  specifying owner, retry logic, and retry delays.
default_args = {
    "owner": "airflow",
    "depends_on_past": False,  # D not depend on the success of previous runs.
    "retries": 2,  # Number of retries for failed tasks.
    "retry_delay": timedelta(seconds=10),  # Time delay between retries.
}

dag = DAG(
    "ELT_with_meltano",
    schedule_interval="@daily",
    # With catchup, will execute the dag several times for testing.
    start_date=datetime(2024, 12, 1),
    # Only one active instance of the DAG at a time.
    max_active_runs=1,
    # This is just for testing, as it will run many times the dag based on the start_date.
    catchup=True,
    # To help the use of params
    render_template_as_native_obj=True,
    # To enable params to be passed to the DAG.
    params={"custom_elt_date": None},
    default_args=default_args,
)

# Task to extract data from
# a CSV source and write it to another CSV.
extract_csv = BashOperator(
    task_id="extract_csv_to_csv",
    bash_command=(
        # Change to the meltano project root directory.
        f"cd {PROJECT_ROOT}; "
        # Set Meltano environment to 'extract'.
        "MELTANO_ENVIRONMENT=extract "
        # Specify the source type as CSV.
        "SOURCE=csv "
        # Use a custom date if provided, otherwise use the execution date.
        "DATESTAMP={{ dag_run.conf['custom_elt_date'] if dag_run.conf.get('custom_elt_date') else ds }} "
        # Run the Meltano extraction job.
        f"{MELTANO_BIN} run extract_csv"
    ),
    dag=dag,
)

# Task to extract data from a PostgreSQL source and write it to a CSV.
extract_postgres = BashOperator(
    task_id="extract_postgres_to_csv",
    bash_command=(
        f"cd {PROJECT_ROOT}; "
        # Load environment variables from the .env file.
        "set -a; source .env; set +a; "
        "MELTANO_ENVIRONMENT=extract "
        # Specify the source type as PostgreSQL.
        "SOURCE=postgres "
        "DATESTAMP={{ dag_run.conf['custom_elt_date'] if dag_run.conf.get('custom_elt_date') else ds }} "
        f"{MELTANO_BIN} run extract_postgres"
    ),
    dag=dag,
)

# Task to load data from CSV into PostgreSQL.
load_to_postgres = BashOperator(
    task_id="load_csv_data_to_postgres",
    bash_command=(
        f"cd {PROJECT_ROOT}; "
        "set -a; source .env; set +a; "
        # Set Meltano environment to 'load'.
        "MELTANO_ENVIRONMENT=load "
        # Specify the target schema in PostgreSQL.
        "SCHEMA=public "
        "EXTRACTED_AT={{ dag_run.conf['custom_elt_date'] if dag_run.conf.get('custom_elt_date') else ds }} "
        f"{MELTANO_BIN} run load_to_postgres"
    ),
    dag=dag,
)

# Both extract tasks must complete before the load task can run.
[extract_csv, extract_postgres] >> load_to_postgres
