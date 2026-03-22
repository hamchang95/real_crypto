# Real Crypto
![high level design](https://raw.githubusercontent.com/hamchang95/real_crypto/89cde42fbd36e730a2c8a0f079c4659a89819ad6/ref/hld.svg)
## Prerequisites

1. Create a free Coinbase Developer Platform account at https://portal.cdp.coinbase.com
2. Generate an API key (free, no trading required - read-only market data is enough)
3. Copy `.env.example` to `.env` and fill in your credentials:

COINBASE_API_KEY=organizations/{org_id}/apiKeys/{key_id}
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n"

git clone <repo>
cp .env.example .env          # fill in GCP service account key
terraform apply               # creates GCS bucket + BQ dataset
docker compose up -d          # starts Redpanda + Flink
python producer/producer_mock.py   # starts sending ticks
visit Streamlit URL to see dashboard