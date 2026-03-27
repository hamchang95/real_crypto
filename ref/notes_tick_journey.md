WebSocket
    │
    │  raw JSON string (nested, messy)
    ▼
tick_from_dict()
    │
    │  Tick (dataclass, in memory)
    ▼
tick_serialiser()
    │
    │  bytes (JSON encoded)
    ▼
Redpanda topic
    │
    │  bytes (stored)
    ▼
SimpleStringSchema()
    │
    │  str (decoded bytes)
    ▼
tick_deserializer()
    │
    │  Tick (dataclass, in Flink)
    ▼
assign_timestamps_and_watermarks()
    │
    │  Tick (same, Flink now knows event time)
    ▼
AddSpread()
    │
    │  EnrichedTick (dataclass, adds spread field)
    ▼
key_by(product_id)
    │
    │  EnrichedTick (same, just routed by product)
    ▼
window()
    │
    │  List[EnrichedTick] (grouped by product + 1min bucket)
    ▼
OHLCVAggregator()
    │
    │  OHLCVRow (dataclass, one per product per minute)
    ▼
BQSink()
    │
    │  dict (dataclasses.asdict, datetime → isoformat string)
    ▼
BigQuery