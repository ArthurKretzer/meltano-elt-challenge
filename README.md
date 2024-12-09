SOURCE=csv TIMESTAMP=$(date +%Y-%m-%d) CSV_FILE_DEFINITION=./extract/extract_csv_files_definition.json meltano schedule run daily-csv-load

SOURCE=postgres TIMESTAMP=$(date +%Y-%m-%d) meltano run tap-postgres target-csv

SCHEMA=public CSV_FILE_DEFINITION=./extract/load_csv_files_definition.json meltano run tap-csv target-postgres
