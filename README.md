# Real Crypto
![high level design](https://raw.githubusercontent.com/hamchang95/real_crypto/89cde42fbd36e730a2c8a0f079c4659a89819ad6/ref/hld.svg)
- Coinbase WebSocket producer sends ticker messages to Redpanda (Kafka-compatible broker).
- Flink consumes messages from Redpanda and runs aggregation job.
- Raw ticks are written to GCS bucket (cold storage, replay insurance).
- Aggregated OHLCV/spread windows are written to BigQuery.
- Streamlit queries BigQuery and displays the dashboard./
[🔗Notes on architecture](https://github.com/hamchang95/real_crypto/blob/main/ref/notes_architecture.md)

## Prerequisites
1. Create a free Coinbase Developer Platform account at https://portal.cdp.coinbase.com
2. Generate an API key (free, no trading required - read-only market data is enough)
3. Copy `.env.example` to `.env` and fill in your credentials

## Steps
- git clone https://github.com/hamchang95/real_crypto.git
- cp .env.example .env          # fill in GCP service account key
- terraform apply               # creates GCS bucket + BQ dataset
- docker compose up -d          # starts Redpanda + Flink
- uv run python flink/src/coinbase_ws.py 30   # duration
- visit Streamlit URL to see dashboard

## Further Work
Docker Compose is sufficient for this project's scope - single node, fixed workload, no multi-machine requirements.

In a production setting, this pipeline would run on Kubernetes with:
- Flink on Kubernetes operator for job lifecycle management
- Redpanda on dedicated nodes with replication factor > 1
- Horizontal pod autoscaling on the taskmanager based on consumer lag