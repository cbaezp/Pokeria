#!/bin/sh
set -e

echo "[pokerlab-entrypoint] Waiting for database to be ready..."

# Wait for postgres connection
python3 -c "
import sys, time
import psycopg

raw_url = '${DATABASE_SYNC_URL}'
clean_url = raw_url.replace('postgresql+psycopg://', 'postgresql://').replace('postgresql+asyncpg://', 'postgresql://')
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg.connect(clean_url)
        conn.close()
        print('[pokerlab-entrypoint] Database is ready!')
        sys.exit(0)
    except Exception as e:
        print(f'[pokerlab-entrypoint] Waiting for database ({i+1}/{max_retries}): {e}')
        time.sleep(1)
sys.exit(1)
"

echo "[pokerlab-entrypoint] Executing service command: $@"
exec "$@"
