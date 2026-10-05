# PostgreSQL with the migrated OpenClinica database and the demo data.
# demo-data.sql.gz is produced by the Demo-Image workflow and is not committed.
# The official image restores it on the first start with an empty data volume.
FROM postgres:11

COPY demo-data.sql.gz /docker-entrypoint-initdb.d/10-demo-data.sql.gz
COPY 20-unlock.sql /docker-entrypoint-initdb.d/20-unlock.sql
