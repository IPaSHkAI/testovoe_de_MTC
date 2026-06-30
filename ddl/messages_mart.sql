CREATE TABLE IF NOT EXISTS default.messages_mart_local ON CLUSTER my_cluster
(
    customer_id UInt32,
    application_uuid UUID,
    message_id UUID,
    sent_date DateTime64(6),
    sender LowCardinality(String),
    receiver UInt64,
    country LowCardinality(String),
    segment_count UInt32,
    delivery_status LowCardinality(String),
    attempt_number UInt8,
    delivery_time UInt16,
    price Decimal(10, 4),
    currency LowCardinality(String),
    receiver_operator LowCardinality(String),
    direction UInt8,
    created_at DateTime64(6),
    updated_at DateTime64(6),
    deleted_at Nullable(DateTime64(6))
)
ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{shard}/messages_mart_local', '{replica}', updated_at)
PARTITION BY toYYYYMM(sent_date)
ORDER BY (sent_date, customer_id, message_id)
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS default.messages_mart ON CLUSTER my_cluster
(
    customer_id UInt32,
    application_uuid UUID,
    message_id UUID,
    sent_date DateTime64(6),
    sender LowCardinality(String),
    receiver UInt64,
    country LowCardinality(String),
    segment_count UInt32,
    delivery_status LowCardinality(String),
    attempt_number UInt8,
    delivery_time UInt16,
    price Decimal(10, 4),
    currency LowCardinality(String),
    receiver_operator LowCardinality(String),
    direction UInt8,
    created_at DateTime64(6),
    updated_at DateTime64(6),
    deleted_at Nullable(DateTime64(6))
)
ENGINE = Distributed(my_cluster, default, messages_mart_local, customer_id);