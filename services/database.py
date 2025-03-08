import pymongo

# MongoDB Connection
MONGO_URI = "mongodb+srv://mosesmacharia084:Newpassword18702@cluster0.gcck2ys.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI)
db = client["ebay_products"]
cache_collection = db["cached_searches"]

print("✅ Connected to MongoDB")

def get_cached_results(query):
    """Retrieve cached results from MongoDB based on the search query."""
    cached = cache_collection.find_one({"query": query})
    if cached:
        return cached.get("results", [])
    return None  # Instead of failing, return None if no cache exists


def cache_results(query, results):
    """Store search results in MongoDB cache, updating if query already exists."""
    cache_collection.update_one(
        {"query": query},  # Find existing query
        {"$set": {"results": results}},  # Update or insert results
        upsert=True  # Create a new document if it doesn't exist
    )
