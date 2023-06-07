#!/bin/sh

wait_database()
{
  HOST=$1
  PORT=$2
  TYPE=$3

  echo "Waiting for $TYPE..."

  while ! nc -z $HOST $PORT; do
    sleep 0.1
  done

  echo "$TYPE started"
}

wait_database $PG_DB_HOST $PG_DB_PORT $DB_TYPE

wait_database $REFRESH_REDIS_HOST $REFRESH_REDIS_PORT $REFRESH_REDIS_TYPE

wait_database $REDIS_HOST $REDIS_PORT $BLOCKLIST_REDIS_TYPE

wait_database $RATE_LIMIT_REDIS_HOST $RATE_LIMIT_REDIS_PORT $RATE_LIMIT_REDIS_TYPE

alembic upgrade head

python3 app.py

exec "$@"
