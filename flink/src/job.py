from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
from pathlib import Path
from pyflink.datastream import SinkFunction, AggregateFunction, StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment
from google.cloud import bigquery
from kafka import KafkaConsumer
from models import tick_deserializer, tick
from datetime import datetime

server = 'localhost:9092'
topic_name = 'ticks'

credentials = service_account.Credentials.from_service_account_file('./99_secrets/svc_infra.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[server],
    auto_offset_reset='earliest',
    group_id='ticks-to-bigquery',
    value_deserializer=tick_deserializer
)

def create_accumulator(self):
    return {
        "spread_sum":  0.0,
        "count":       0,
        "volume_sum":  0.0,
        "price":       0.0,
        "high_24h":    0.0,   
        "low_24h":     0.0,   
        "product_id":  None,  
    }

def add(self, tick, accumulator):
    spread = tick.best_ask - tick.best_bid
    accumulator["spread_sum"] += spread
    accumulator["count"]      += 1
    accumulator["volume_sum"] += tick.volume_24h
    accumulator["price"]       = tick.price
    accumulator["high_24h"]    = tick.high_24h   # just overwrite — stable within window
    accumulator["low_24h"]     = tick.low_24h
    accumulator["product_id"]  = tick.product_id
    return accumulator

def get_result(self, accumulator):
    avg_spread     = accumulator["spread_sum"] / accumulator["count"]
    day_vlty = (accumulator["high_24h"] - accumulator["low_24h"]) / accumulator["low_24h"]
    denom = accumulator["high_24h"] - accumulator["low_24h"]
    ind_vlty = (accumulator["price"] - accumulator["low_24h"]) / denom if denom != 0 else None

    return {
        "product_id":    accumulator["product_id"],
        "price":         accumulator["price"],
        "avg_spread":    avg_spread,
        "volume":        accumulator["volume_sum"],
        "high_24h":      accumulator["high_24h"],
        "low_24h":       accumulator["low_24h"],
        "day_vlty": day_vlty,
        "ind_vlty": ind_vlty,
    }

def insert_tick(row: dict):
    spread = round(row["best_ask"] - row["best_bid"], 8)
    day_vlty = (row["high_24h"] - row["low_24h"]) / row["low_24h"]
    ind_vlty = (row["price"] - row["low_24h"]) / (row["high_24h"] - row["low_24h"])

    sql = f"""
        INSERT INTO `{client.project}.crypto.spread`
          (product_id, window_start, price, low_24h, high_24h, price_per_chg_24h, volume, best_ask, best_bid, spread, day_vlty, ind_vlty)
        VALUES (
            '{row["product_id"]}',
            TIMESTAMP '{row["timestamp"]}',
            {row["price"]},
            {row["low_24h"]},
            {row["high_24h"]},
            {row["price_per_chg_24h"]},
            {row["volume"]},
            {row["best_ask"]},
            {row["best_bid"]},
            {spread},
            {day_vlty},
            {ind_vlty}
        )
    """
    client.query(sql).result()
    print(f"Inserted: {row['product_id']} {row['window_start']}")

if __name__ == '__main__':
    insert_tick()