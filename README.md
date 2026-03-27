# Real-Time Crypto Analytics Pipeline
This repo is a project repository for real-time pipeline of cryptocurrency market.

## Problem Description

Cryptocurrency markets move fast - prices and spreads shift within seconds across hundreds of trading pairs. For traders and analysts, having a real-time view of market conditions is essential for making informed decisions.

This project builds an end-to-end streaming data pipeline that ingests 
live ticker data from Coinbase across 320+ USD trading pairs, processes 
it in real-time using Apache Flink, and delivers a dashboard showing:

- Which coins have the widest bid-ask spreads (liquidity indicator)
- How average price, spread, and volatility evolve minute by minute
- A volatility indicator showing where each coin's price sits within its 24-hour range

The pipeline processes data with sub-minute latency — from Coinbase WebSocket to BigQuery in under 60 seconds — giving traders and analysts an up-to-date view of market microstructure across the entire Coinbase USD market.

> 💡 **Bid-Ask Spread**: The difference between the lowest price a seller will accept and the highest a buyer will pay. A narrow spread indicates high liquidity; a wide spread signals low liquidity or high uncertainty.\
> 💡 **Volatility Indicator**:The indicator that shows where the current price sits within  the coin's 24-hour high-low range.A value near 1 means the price is close to its daily high, near 0 means it's close to its daily low.\
> 💡 **OHLCV**: Open, High, Low, Close, Volume - standard financial data format for summarising price action over a time window.

## Architecture
![High Level Design](https://github.com/hamchang95/real_crypto/blob/main/ref/hld.svg)

## Technologies Used
| Component | Technology | Purpose |
|---|---|---|
| Data Source | Coinbase WebSocket API | Live ticker feed for 320+ USD trading pairs |
| Message Broker | Redpanda (Kafka-compatible) | Decouples producer from processing, buffers tick messages |
| Stream Processor | Apache Flink (PyFlink) | 1-minute tumbling window aggregations |
| Data Lake | Google Cloud Storage | Raw tick storage for reprocessing |
| Data Warehouse | Google BigQuery | Aggregated OHLCV windows, partitioned by day, clustered by product |
| Dashboard | Looker Studio | Real-time visualisation of market microstructure |
| Infrastructure | Terraform | Cloud resource provisioning |
| Containerisation | Docker Compose | Local orchestration of Flink and Redpanda |

## Data Pipeline
![High Level Design](https://github.com/hamchang95/real_crypto/blob/main/ref/lld.svg)

### 1. Ingestion
A Python producer connects to the Coinbase WebSocket API and subscribes to the ticker channel for 320+ USD trading pairs. Each ticker message is validated, parsed into a `Tick` object, serialised to JSON bytes and sent to a Redpanda topic.

### 2. Stream Processing
Apache Flink (PyFlink) consumes tick messages from Redpanda and runs 
the following transformations:

1. **Deserialise**: bytes → `Tick` object
2. **Enrich**:`Tick` → `EnrichedTick` (adds bid-ask spread)
3. **Key by**: partition stream by `product_id` (320 sub-streams)
4. **Window**: 1-minute tumbling event-time windows per product
5. **Aggregate**: compute OHLCV metrics per window → `OHLCVRow`
6. **Sink**: write to BigQuery via Google Cloud Python SDK

### 3. Storage
- **Raw ticks** → Google Cloud Storage (for reprocessing/auditing)
- **Aggregated OHLCV windows** → BigQuery, partitioned by day on 
  `window_start`, clustered by `product_id`

## Dashboard
Looker Studio connects directly to BigQuery and refreshes automatically, displaying:
- Top 5 coins by average bid-ask spread (categorical)
- Average price, spread and volatility over time (temporal)

## Reproducing the Project

### Prerequisites
- Docker and Docker Compose installed
- Google Cloud account with BigQuery and GCS enabled
- Coinbase Advanced Trade API key and secret
- Terraform installed

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

### 2. Set Up Google Cloud
1. Create a GCP project
2. Create a service account with the following roles:
   - BigQuery Admin
   - Storage Admin
3. Download the service account JSON key and save to `99_secrets/svc_infra.json`

### 3. Provision Infrastructure with Terraform
```bash
cd terraform
terraform init
terraform plan
terraform apply
```
This creates:
- BigQuery dataset and table (partitioned by day, clustered by product_id)
- GCS bucket for raw ticks

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
```

### 5. Start the Pipeline
```bash
docker compose up -d
```
This starts:
- Redpanda (message broker)
- Flink JobManager
- Flink TaskManager

### 6. Create Redpanda Topic
```bash
docker exec real_crypto-redpanda-1 rpk topic create ticks \
    --partitions=50 \
    --replicas=1
```

> [!NOTE]
> 50 partitions allows Flink to parallelise consumption across all 15 
> task slots with room to scale. Replicas is set to 1 since this is a 
> single-node Redpanda instance.

### 7. Submit the Flink Job
```bash
docker exec real_crypto-jobmanager-1 flink run \
    -py /opt/flink/src/consume_ticks_tumble.py \
    -pyfs /opt/flink/src
```

### 8. Start the Producer
Install dependencies using uv:
```bash
uv sync
```
This project has two separate dependency sets:

| File | Purpose |
|---|---|
| `pyproject.toml` | Producer dependencies (runs locally via uv) |
| `flink/pyproject.flink.toml` | PyFlink job dependencies (runs inside Docker) |

The Flink dependencies are installed automatically when the Docker image is built.
You only need to run `uv sync` for the producer.

Run producer for 1 hour:
```bash
uv run python producer.py 3600
```

> [!NOTE]
> The duration argument is in seconds. 3600 = 1 hour. Adjust as needed.

### 9. View the Dashboard
[Looker Studio Dashboard](url)

## Project Structure
```
real_crypto/
├── flink/
│   ├── src/
│   │   ├── consume_ticks_tumble.py    # PyFlink job — stream processing pipeline
│   │   └── models.py                  # Tick, EnrichedTick, OHLCVRow dataclasses
│   ├── Dockerfile.flink               # Flink image with PyFlink and connector JARs
│   ├── flink-config.yaml              # Flink cluster configuration
│   └── pyproject.flink.toml          # PyFlink job dependencies
├── terraform/
│   ├── main.tf                        # BigQuery dataset, table, GCS bucket
│   ├── variables.tf                   
│   └── outputs.tf                     
├── prometheus/
│   └── prometheus.yml                 # Flink metrics scraping config
├── 99_secrets/                        # GCP service account key (gitignored)
│   └── svc_infra.json                
├── producer.py                        # Coinbase WebSocket → Redpanda producer
├── docker-compose.yml                 # Redpanda, Flink JobManager, TaskManager
├── pyproject.toml                     # Producer dependencies
├── .env.example                       # Environment variable template
├── .gitignore                         
└── README.md                          
```