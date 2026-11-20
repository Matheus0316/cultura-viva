#!/usr/bin/env bash
set -e

# Remove possíveis quebras de linha Windows automaticamente (extra seguro)
# (isso evita erro mesmo se você esquecer de converter)
sed -i 's/\r$//' "$0" 2>/dev/null || true

echo "Waiting for postgres..."

# Aguarda o banco ficar disponível
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done

echo "PostgreSQL started"

# Migrations
echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

# Static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Somente executa migrações e superuser se o comando for runserver ou se for explicitamente solicitado
if [[ "$*" == *"runserver"* ]] || [ -z "$*" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Creating superuser (if not exists)..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
username = "admin"
email = "admin@email.com"
password = "admin"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created")
else:
    print("Superuser already exists")
END
fi

# Start
if [ -z "$*" ]; then
    echo "Starting default server..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Executing: $@"
    exec "$@"
fi
