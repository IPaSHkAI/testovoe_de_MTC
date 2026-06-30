FROM apache/superset:4.0.1

USER root
RUN pip install clickhouse-connect

COPY superset_init.sh /app/superset_init.sh
RUN chmod +x /app/superset_init.sh

USER superset