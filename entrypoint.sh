#!/bin/sh
set -e

echo "⏳ Waiting for Postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
  sleep 1
done
echo "✅ Postgres is ready!"

# if [ -f /app/init.sql ]; then
#   echo "🚀 Running database initialization script..."
#   psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -f /app/init.sql
#   echo "🎉 Database initialized!"
# else
#   echo "⚠️ No init.sql found, skipping DB initialization."
# fi

echo "🐍 Starting bot..."
exec python3 ./app.py