#!/bin/bash
set -e

echo "Шаг 1: Накатываем миграции во внутреннюю БД Superset..."
superset db upgrade

echo "Шаг 2: Создаем администратора..."
superset fab create-admin \
    --username admin \
    --firstname Superset \
    --lastname Admin \
    --email admin@localhost \
    --password admin || true

echo "Шаг 3: Инициализируем стандартные роли и разрешения..."
superset init

echo "Шаг 4: Импортируем готовый дашборд..."
DASHBOARD_PATH="/superset/app/dashboard_export.zip"

if [ -f "$DASHBOARD_PATH" ]; then
    echo "Импорт дашборда..."
    superset import-dashboards --path "$DASHBOARD_PATH" -u admin
    
    echo "Шаг 4.5: Инжектим пароль ClickHouse во внутреннюю метабазу..."
    superset shell <<EOF
from superset import db
from superset.models.core import Database
for database in db.session.query(Database).all():
    if 'ch-node1' in database.sqlalchemy_uri:
        database.password = 'secret_password'
db.session.commit()
EOF
    echo "Дашборд успешно импортирован, пароль обновлен!"
else
    echo "Предупреждение: файл дашборда не найден по пути $DASHBOARD_PATH"
fi

echo "Шаг 5: Запуск веб-сервера Superset..."
exec superset run -p 8088 -h 0.0.0.0 --with-threads