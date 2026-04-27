from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import os

def create_topics(server: str, topics: list[dict]):
    server = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    admin_client = KafkaAdminClient(bootstrap_servers=[server])
    
    new_topics = [
        NewTopic(
            name=t["name"],
            num_partitions=t["num_partitions"],
            replication_factor=t["replication_factor"]
        )
        for t in topics
    ]
    
    try:
        admin_client.create_topics(new_topics)
        print(f"Topics created: {[t['name'] for t in topics]}")
    except TopicAlreadyExistsError:
        print("Topics already exist, skipping")
    finally:
        admin_client.close()

# call this before starting the producer
create_topics(
    server="localhost:29092",
    topics=[
        {"name": "ticks",              "num_partitions": 45, "replication_factor": 1},
        {"name": "ticks-dead-letter",  "num_partitions": 1,  "replication_factor": 1}
    ]
)