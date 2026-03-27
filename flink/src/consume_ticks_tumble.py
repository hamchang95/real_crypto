from google.cloud import bigquery
from google.oauth2 import service_account
from models import tick_deserializer, Tick, EnrichedTick, OHLCVRow
from pathlib import Path
from datetime import datetime, timezone
from pyflink.datastream import MapFunction, ProcessWindowFunction, StreamExecutionEnvironment, SinkFunction
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common import Duration
from pyflink.common.time import Time
from pyflink.common.watermark_strategy import TimestampAssigner
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer, KafkaSource
from pyflink.datastream.window import TumblingEventTimeWindows
import dataclasses

server = 'redpanda:9092' 
topic_name = 'ticks'

class AddSpread(MapFunction):
    def map(self, t: Tick) -> EnrichedTick:
        return EnrichedTick(
            spread=t.best_ask - t.best_bid,
            **dataclasses.asdict(t)
        )

class OHLCVAggregator(ProcessWindowFunction):
    def process(self, key, ctx, elements):
        ticks = sorted(elements, key=lambda t: t.timestamp)
        
        prices = [t.price for t in ticks]
        avg_price = sum(prices) / len(prices)
        price_high = max(prices)  # highest tick price in the window
        price_low  = min(prices)  # lowest tick price in the window
        volumes = [t.volume_24h for t in ticks]
        avg_volume = sum(volumes)/ len(volumes)
        spreads = [t.spread for t in ticks]
        avg_spread = sum(spreads)/ len(spreads)
        highs = [t.high_24h for t in ticks]
        high_24h = max(highs)
        lows = [t.low_24h for t in ticks]
        low_24h = min(lows)
        ind_vlty = (avg_price - low_24h) / (high_24h - low_24h) if high_24h != low_24h else None
        
        yield OHLCVRow(
            product_id=key,
            window_start=datetime.fromtimestamp(ctx.window().start / 1000, tz=timezone.utc),
            window_end=datetime.fromtimestamp(ctx.window().end / 1000, tz=timezone.utc),
            price_open=prices[0],
            price_close=prices[-1],
            price_high = price_high,
            price_low=price_low,
            avg_price = avg_price,
            avg_volume = avg_volume,
            avg_spread = avg_spread,
            ind_vlty = ind_vlty,
            high_24h = high_24h,
            low_24h = low_24h
        )

class BQSink(MapFunction):
    def open(self, runtime_context):
        credentials = service_account.Credentials.from_service_account_file(
            '/99_secrets/svc_infra.json'
        )
        self.client = bigquery.Client(credentials=credentials)
        self.table_ref = f"{credentials.project_id}.crypto.ohlcv"

    def map(self, row: OHLCVRow):
        record = dataclasses.asdict(row)
        record['window_start'] = row.window_start.isoformat()
        record['window_end'] = row.window_end.isoformat()
        
        errors = self.client.insert_rows_json(self.table_ref, [record])
        if errors:
            raise RuntimeError(f"BQ insert error: {errors}")
        
        return row  # map must return something
        
class TickTimestampAssigner(TimestampAssigner):
    def extract_timestamp(self, tick: Tick, _: int) -> int:
        return tick.timestamp  # already in milliseconds from tick_from_dict


def main():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(60 * 1000)
    env.set_parallelism(15)

    # Set up Kafka source
    source = KafkaSource.builder() \
    .set_bootstrap_servers(server) \
    .set_topics(topic_name) \
    .set_group_id('source') \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

    # Define Watermark Strategy
    watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(5)) \
    .with_timestamp_assigner(TickTimestampAssigner())

    env.from_source(source, WatermarkStrategy.no_watermarks(), "Redpanda") \
        .map(lambda raw: tick_deserializer(raw)) \
        .assign_timestamps_and_watermarks(watermark_strategy) \
        .map(AddSpread()) \
        .key_by(lambda t: t.product_id) \
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))\
        .process(OHLCVAggregator()) \
        .map(BQSink())
    
    env.execute("coinbase-ohlcv")

if __name__ == "__main__":
    main()