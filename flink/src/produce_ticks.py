from coinbase.websocket import WSClient
from coinbase import jwt_generator
from dotenv import load_dotenv
import time
import datetime as dt
import os
import sys
from models import Tick, tick_from_dict, tick_serialiser
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import requests
import json

# set up
load_dotenv()
topic_name = 'ticks'
server = "localhost:29092"
duration = int(sys.argv[1])

def get_usd_products() -> list[str]:
    """Fetch all active USD trading pairs from Coinbase REST API."""
    # build jwt token needed for the call
    api_key      = os.getenv('COINBASE_API_KEY')
    api_secret     = os.getenv('COINBASE_API_SECRET')
    request_method = "GET"
    request_path   = "/api/v3/brokerage/products"
    jwt_uri = jwt_generator.format_jwt_uri(request_method, request_path)
    jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, api_secret)

    # call the api
    response = requests.get(
        'https://api.coinbase.com/api/v3/brokerage/products',
        headers={'Authorization': f'Bearer {jwt_token}'}
    )

    if response.status_code==200:
        products = response.json().get("products", [])
    else:
        raise ConnectionError(response.status_code)
    
    return [
        p["product_id"]
        for p in products
        if p["quote_currency_id"] == "USD"
        and p["status"] == "online"
        and not p.get("is_disabled", False)
    ]

def make_producer(server: str):
        for attempt in range(10):
            try:
                return KafkaProducer(
                    bootstrap_servers=[server],
                    value_serializer=tick_serialiser,
                    request_timeout_ms=20000,
                )
            except NoBrokersAvailable:
                print(f"Broker not ready, retrying... ({attempt + 1}/10)")
                time.sleep(3)
        raise RuntimeError("Could not connect to broker")

def main():
    # set up kafka producer
    producer = make_producer(server=server)

    products = get_usd_products()
    print(f"Subscribing to {len(products)} products")

    # set up websocket
    key = os.getenv('COINBASE_API_KEY')
    secret = os.getenv('COINBASE_API_SECRET')

    def on_message(msg):
        try:
            ticks = tick_from_dict(msg)
            if not ticks:
                return
            for t in ticks:
                producer.send(topic_name, value=t)
                print(f'Sent {t}')
        except ValueError as e:
            # route to dead letter
            producer.send(
                'ticks-dead-letter',
                value=json.dumps({
                    "raw_message": msg,
                    "error": str(e),
                    "timestamp": dt.datetime.utcnow().isoformat()
                }).encode()
            )
            print(f'Dead lettered malformed message: {e}')
        except Exception as e:
            # unexpected error - log but don't crash the connection
            print(f'Unexpected error processing message: {e}')

    def on_open():
        print("Connection opened!")

    # set up client
    client = WSClient(api_key=key, api_secret=secret, on_message=on_message, on_open=on_open)
    
    # open the connection and subscribe to the ticker channel 
    client.open()
    client.subscribe(product_ids=products, channels=["ticker"])

    # wait for the defined duration
    time.sleep(duration)

    # unsubscribe from the ticker channel and close the connection
    client.unsubscribe(product_ids=products, channels=["ticker"])
    client.close()

    producer.flush()
    print("Done")

if __name__ == '__main__':
    main()