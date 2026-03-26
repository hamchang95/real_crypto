from google.cloud import bigquery
from google.oauth2 import service_account
from kafka import KafkaConsumer
from models import tick_deserializer
from pathlib import Path
from datetime import datetime, timezone

server = 'localhost:29092' # using external port as this file is run by WSL 
topic_name = 'ticks'

credentials = service_account.Credentials.from_service_account_file('./99_secrets/svc_infra.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)
print(client.project)

consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[server],
    auto_offset_reset='earliest',
    group_id='ticks-to-bigquery',
    value_deserializer=tick_deserializer
)

def insert_tick(t):
    spread = round(t.best_ask - t.best_bid, 8)
    day_vlty = (t.high_24h - t.low_24h) / t.low_24h
    ind_vlty = (t.price - t.low_24h) / (t.high_24h - t.low_24h)
    # convert ms epoch to BigQuery timestamp string
    ts = datetime.fromtimestamp(t.timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    sql = f"""
        INSERT INTO `{client.project}.crypto.ticker`
          (product_id, timestamp, price, low_24h, high_24h,
           price_per_chg_24h, volume_24h, best_ask, best_bid, spread,
           day_vlty, ind_vlty)

        VALUES (
            '{t.product_id}',
            TIMESTAMP '{ts}',
            {t.price},
            {t.low_24h},
            {t.high_24h},
            {t.price_per_chg_24h},
            {t.volume_24h},
            {t.best_ask},
            {t.best_bid},
            {spread},
            {day_vlty},
            {ind_vlty}
        )
    """
    try:
        client.query(sql).result()
        print(f"Inserted: {t.product_id} {ts}")
    except Exception as e:
        print(f'BigQuery error: {e}')

if __name__ == '__main__':
    print("Consuming ticks...")
    for message in consumer:
        t = message.value
        if t is None:
            print('Failed to deserialise message')
            continue
        insert_tick(t)