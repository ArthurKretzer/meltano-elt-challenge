docker compose up -d

docker compose down -v

MELTANO_ENVIRONMENT=extract SOURCE=csv DATESTAMP=$(date +%Y-%m-%d) meltano run tap-csv target-csv
MELTANO_ENVIRONMENT=extract SOURCE=csv DATESTAMP=$(date +%Y-%m-%d) meltano run extract_csv

MELTANO_ENVIRONMENT=extract SOURCE=postgres DATESTAMP=$(date +%Y-%m-%d) meltano run tap-postgres target-csv
MELTANO_ENVIRONMENT=extract SOURCE=csv DATESTAMP=$(date +%Y-%m-%d) meltano run extract_postgres

MELTANO_ENVIRONMENT=load SCHEMA=public EXTRACTED_AT=$(date +%Y-%m-%d) meltano run tap-csv target-postgres

meltano invoke airflow:initialize
meltano invoke airflow users create -u admin@localhost -p password --role Admin -e admin@localhost -f admin -l admin

meltano invoke airflow webserver
meltano invoke airflow scheduler