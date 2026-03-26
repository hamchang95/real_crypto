from coinbase import jwt_generator
from dotenv import load_dotenv
import time
import datetime as dt
import os
import sys
import requests

# set up
load_dotenv()

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

def main():
    products = get_usd_products()
    print(f"Subscribing to {len(products)} products")

if __name__ == '__main__':
    main()