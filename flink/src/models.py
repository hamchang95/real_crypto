import datetime as dt
import dataclasses
from dataclasses import dataclass
import json

fields = {'timestamp', 'type', 'product_id', 'price', 
          'volume_24_h', 'low_24_h', 'high_24_h', 'price_percent_chg_24_h',
          'best_ask', 'best_bid'}

@dataclass
class tick:
    timestamp: int
    type: str
    product_id: str
    price: float
    volume_24h: float
    low_24h: float
    high_24h: float
    price_per_chg_24h: float
    best_ask: float
    best_bid: float

def tick_from_dict(raw: str) -> tick:
    # flatten out fields into a dictionary
    raw = json.loads(raw)

    if raw.get('channel') != 'ticker':
        return None
    
    for event in raw.get('events', []):
        tickers = event.get('tickers', [])
        for ticker in tickers:
            d = {
                'timestamp': raw['timestamp'],
                'type': event['type'],
                'product_id': ticker['product_id'],
                'price': ticker['price'],
                'volume_24_h': ticker['volume_24_h'],
                'low_24_h': ticker['low_24_h'],
                'high_24_h': ticker['high_24_h'],
                'price_percent_chg_24_h': ticker['price_percent_chg_24_h'],
                'best_ask': ticker['best_ask'],
                'best_bid': ticker['best_bid']
            }

            # raise missing fields error
            missing = fields - d.keys()
            if missing:
                raise ValueError(f'Missing fields: {missing}')
            
            # check if timestamp is correctly formatted
            ts = d['timestamp']
            
            if not dt.datetime.fromisoformat(ts):
                raise ValueError(f'Timestamp is not correctly fomratted: {ts}')
            else:
                ts = dt.datetime.fromisoformat(ts).timestamp()
                ts_num = int(ts*1000)
            # check if the type is either snapshot or update
            if d['type'] not in ('snapshot', 'update'):
                raise ValueError(f'Invalid type: {d['type']}')

            # check if numeric fields are positive
            price = float(d['price'])
            volume = float(d['volume_24_h'])
            low = float(d['low_24_h'])
            high = float(d['high_24_h'])
            chg = float(d['price_percent_chg_24_h'])
            best_ask = float(d['best_ask'])
            best_bid = float(d['best_bid'])
            num_fields = [price, volume, low, high, best_ask, best_bid]

            if any(f<=0 for f in num_fields):
                raise ValueError(f'Non-positive numeric field: {price}, {volume}, {low}, {high}, {chg}, {best_ask}, {best_bid}')
            
            return tick(
                timestamp=ts_num,
                type = d['type'],
                product_id = d['product_id'],
                price = price,
                volume_24h= volume,
                low_24h=low,
                high_24h=high,
                price_per_chg_24h=chg,
                best_ask = best_ask,
                best_bid = best_bid
            )

def tick_serialiser(data) -> bytes:
    return json.dumps(dataclasses.asdict(data)).encode('utf-8')

def tick_deserializer(data) -> tick:
    json_str = data.decode('utf-8')
    tick_dict = json.loads(json_str)
    return tick(**tick_dict)