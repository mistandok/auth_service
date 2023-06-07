#!/bin/sh

python -u utils/wait_for_psql.py
pytest ./src/

exec "$@"
