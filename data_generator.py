import os
import uuid
import random
import time
from datetime import datetime, timedelta
import clickhouse_connect

# 1. Настройки подключения
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 8123))
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'secret_password')
TABLE_NAME = os.getenv('TABLE_NAME', 'default.messages_mart')

TOTAL_ROWS = 1_000_000
BATCH_SIZE = 100_000

# 2. Справочники для LowCardinality полей
COUNTRIES = ["Russian Federation", "Kazakhstan", "Azerbaijan", "Kyrgyzstan", "Tajikistan", "Belarus", "Uzbekistan", "Armenia", "Georgia", "Israel", "Moldova", "Abkhazia", "not_defined"]
CURRENCIES = ["USD"]
OPERATORS = ["MTS", "Beeline", "MegaFon", "Azercell", "MKS", "Tele2", "All networks", "MEGACOM(Alfa Telecom)", "Indigo Tajikistan", "Beeline (Sky Mobile)", "K-Cell", "O!(Nurtelecom)", "Scartel", "MobiUZ (MTS)", "velcom", "Altel", "not_defined"]
STATUSES = ["DELIVRD", "UNDELIV", "EXPIRED", "NO ROUTES", "SENT", "ROUTE FAILED", "REJECTD", "VND CHN NOT BND", "SUBMIT_RESP TIMEOUT", "UNKNOWN"]
SENDERS = ["Google", "Steam", "Amazon", "PayPal", "Uber", "WhatsApp", "Meta", "Grab", "Airbnb", "Netflix", "LinkedIn", "Outlook", "Twilio", "DHL", "Vodafone", "monitoring", "Spotify", "Bolt", "not_defined"]

def generate_batch(batch_size, start_time, total_seconds):
    """Генерирует пачку синтетических данных"""
    data = []
    
    for _ in range(batch_size):
        # Временной интервал равномерно распределяем в пределах 1 года
        random_offset = random.randint(0, total_seconds)
        random_microsecond = random.randint(0, 999999)
        sent_date = start_time + timedelta(seconds=random_offset, microseconds=random_microsecond)
        
        # Метаданные времени
        created_at = sent_date
        updated_at = sent_date + timedelta(seconds=random.randint(1, 10))
        # 2% сообщений пусть будут "удалены"
        deleted_at = updated_at + timedelta(seconds=5) if random.random() < 0.02 else None
        
        row = [
            random.randint(10000, 99999),             # customer_id (UInt32)
            uuid.uuid4(),                             # application_uuid (UUID)
            uuid.uuid4(),                             # message_id (UUID)
            sent_date,                                # sent_date (DateTime64)
            random.choice(SENDERS),                   # sender (LowCardinality Nullable String)
            random.randint(79000000000, 79999999999), # receiver (UInt64)
            random.choice(COUNTRIES),                 # country (LowCardinality Nullable String)
            random.randint(1, 4),                     # segment_count (UInt32)
            random.choice(STATUSES),                  # delivery_status (LowCardinality Nullable String)
            random.randint(1, 3),                     # attempt_number (UInt8)
            random.randint(0, 300),                   # delivery_time (UInt16)
            round(random.uniform(0.01, 0.75), 4),     # price (Float32)
            random.choice(CURRENCIES),                # currency (LowCardinality Nullable String)
            random.choice(OPERATORS),                 # receiver_operator (LowCardinality Nullable String)
            random.choice([0, 1]),                    # direction (UInt8)
            created_at,                               # created_at (DateTime64)
            updated_at,                               # updated_at (DateTime64)
            deleted_at                                # deleted_at (Nullable DateTime64)
        ]
        data.append(row)
        
    return data

def main():
    print(f"Подключение к ClickHouse ({CLICKHOUSE_HOST}:{CLICKHOUSE_PORT})...")
    
    # Делаем несколько попыток подключения на случай микрозадержек сети в Docker
    client = None
    for attempt in range(1, 6):
        try:
            client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                username=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD
            )
            print("Успешно подключено к ClickHouse!")
            break
        except Exception as e:
            print(f"Попытка {attempt}/5 не удалась. Ждем 3 секунды... Ошибка: {e}")
            time.sleep(3)
            
    if not client:
        print("Не удалось подключиться к ClickHouse после 5 попыток. Выход.")
        return

    # Временной интервал: 2025 год
    start_time = datetime(2025, 1, 1, 0, 0, 1)
    end_time = datetime(2026, 1, 1, 0, 0, 0)
    total_seconds = int((end_time - start_time).total_seconds())

    print(f"Генерируем данные за период: {start_time.date()} -> {end_time.date()}")
    
    columns = [
        'customer_id', 'application_uuid', 'message_id', 'sent_date', 'sender',
        'receiver', 'country', 'segment_count', 'delivery_status', 'attempt_number',
        'delivery_time', 'price', 'currency', 'receiver_operator', 'direction',
        'created_at', 'updated_at', 'deleted_at'
    ]

    start_generation = time.time()
    batches_count = TOTAL_ROWS // BATCH_SIZE

    for i in range(batches_count):
        batch_start_time = time.time()
        
        batch_data = generate_batch(BATCH_SIZE, start_time, total_seconds)
        client.insert(TABLE_NAME, batch_data, column_names=columns)
        
        print(f"Батч {i+1}/{batches_count} ({BATCH_SIZE} строк) успешно записан за {time.time() - batch_start_time:.2f} сек.")

    print("---")
    print("Готово! 1 000 000 строк успешно загружены.")
    print(f"Общее время выполнения: {time.time() - start_generation:.2f} сек.")

    # Проверка финального количества строк
    result = client.query(f"SELECT count() FROM {TABLE_NAME}")
    print(f"Текущее количество строк в таблице: {result.first_row[0]}")

if __name__ == '__main__':
    main()