import pymongo
import datetime  # ✅ Import datetime

# MongoDB Connection
MONGO_URI = "mongodb+srv://mosesmacharia084:Newpassword18702@cluster0.gcck2ys.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI)
db = client["ebay_products"]

# Collections
cache_collection = db["cached_searches"]  # Stores cached product searches
user_searches_collection = db["user_searches"]  # Stores recent user searches
trending_collection = db["trending_products"]  # ✅ New collection for trending tracking

print("✅ Connected to MongoDB")

def get_cached_results(query):
    """Retrieve cached results from MongoDB based on the search query."""
    cached = cache_collection.find_one({"query": query})
    if cached:
        return cached.get("results", [])
    return None  

def cache_results(query, results):
    """Store search results in MongoDB cache, updating if query already exists."""
    cache_collection.update_one(
        {"query": query},  
        {"$set": {"results": results}},  
        upsert=True  
    )

def store_user_search(query, results):
    """Store recent user searches for trending products."""
    user_searches_collection.insert_one({
        "query": query,
        "results": results[:6],  
        "timestamp": datetime.datetime.utcnow()
    })

def track_product_interaction(product_id, title):
    """✅ Track clicks & searches for trending products."""
    trending_collection.update_one(
        {"_id": product_id},
        {"$inc": {"clicks": 1}, "$set": {"title": title, "last_updated": datetime.datetime.utcnow()}},  
        upsert=True
    )

def get_trending_products(limit=12):
    """✅ Retrieve trending products sorted by most clicks."""
    return list(trending_collection.find().sort("clicks", -1).limit(limit))
