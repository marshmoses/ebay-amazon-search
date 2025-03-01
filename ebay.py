from flask import Flask, request, jsonify
import pymongo
import requests
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client["ebay_products"]
collection = db["products"]

# eBay API Credentials
EBAY_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_HEADERS = {"Authorization": f"Bearer {EBAY_ACCESS_TOKEN}"}

# Cache expiration (in hours)
CACHE_EXPIRY_HOURS = 24

def fetch_ebay_products(query):
    """Fetch products from eBay API."""
    params = {"q": query, "limit": 5}
    response = requests.get(EBAY_API_URL, headers=EBAY_HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("itemSummaries", [])
    return []

@app.route("/search", methods=["GET"])
def search_products():
    """Search for products in MongoDB or fetch fresh data if expired."""
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Check MongoDB for cached data
    cached_result = collection.find_one({"search_query": query})
    
    if cached_result:
        last_updated = cached_result.get("timestamp")
        if last_updated:
            time_diff = datetime.datetime.utcnow() - last_updated
            if time_diff.total_seconds() < CACHE_EXPIRY_HOURS * 3600:
                return jsonify({"source": "cache", "products": cached_result["results"]})

    # Fetch fresh data from eBay
    ebay_results = fetch_ebay_products(query)
    
    # Store in MongoDB with timestamp
    collection.update_one(
        {"search_query": query},
        {"$set": {"results": ebay_results, "timestamp": datetime.datetime.utcnow()}},
        upsert=True
    )

    return jsonify({"source": "API", "products": ebay_results})

if __name__ == "__main__":
    app.run(debug=True)
