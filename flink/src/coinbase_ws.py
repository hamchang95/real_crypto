from coinbase.websocket import WSClient
from dotenv import load_dotenv
import time
import datetime as dt
import os
import sys
from models import tick, tick_from_dict, tick_serialiser
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# set up
load_dotenv()
topic_name = 'ticks'
server = "localhost:29092"
duration = int(sys.argv[1])

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

    # set up websocket
    key = os.getenv('COINBASE_API_KEY')
    secret = os.getenv('COINBASE_API_SECRET')

    def on_message(msg):
        t = tick_from_dict(msg)
        if t is None:
            return   
        producer.send(topic_name, value=t)
        print(f'Sent {t}')

    def on_open():
        print("Connection opened!")

    # set up client
    client = WSClient(api_key=key, api_secret=secret, on_message=on_message, on_open=on_open)
    
    # open the connection and subscribe to the ticker channel 
    client.open()
    client.subscribe(product_ids=["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "USDT-USD"], channels=["ticker"])

    # wait for the defined duration
    time.sleep(duration)

    # unsubscribe from the ticker channel and close the connection
    client.unsubscribe(product_ids=["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "USDT-USD"], channels=["ticker"])
    client.close()

    producer.flush()
    print("Done")

if __name__ == '__main__':
    main()