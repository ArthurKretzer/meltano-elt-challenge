MELTANO_ENVIRONMENT=extract SOURCE=csv TIMESTAMP=$(date +%Y-%m-%d) meltano run tap-csv target-csv

MELTANO_ENVIRONMENT=extract SOURCE=postgres TIMESTAMP=$(date +%Y-%m-%d) meltano run tap-postgres target-csv

MELTANO_ENVIRONMENT=load SCHEMA=public EXTRACTED_AT=$(date +%Y-%m-%d) meltano run tap-csv target-postgres
