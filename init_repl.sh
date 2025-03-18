#!/bin/bash

pg_basebackup -h db -U ${DB_REPL_USER} --pgdata=/var/lib/postgresql/13/main -v -P -X stream

echo "standby_mode = 'on'" >> /var/lib/postgresql/13/main/recovery.conf
echo "primary_conninfo = 'host=db port=5432 user=${DB_REPL_USER} password=${DB_REPL_PASSWORD} sslmode=disable'" >> /var/lib/postgresql/13/main/recovery.conf
echo "trigger_file = '/tmp/postgres.trigger'" >> /var/lib/postgresql/13/main/recovery.conf

service postgresql start

