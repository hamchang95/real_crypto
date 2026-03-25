import requests
import pandas as pd

resp = requests.get("https://api.coinbase.com/api/v3/brokerage/market/products")
products = resp.json()["products"]

# Filter to just spot markets that are online
spot = [
    p for p in products
    if p["product_type"] == "SPOT"
    and p["status"] == "online"
]

spot = pd.DataFrame(spot)

spot.to_csv('1_data/spot.csv', index=False)