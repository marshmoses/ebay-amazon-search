from services.database import cache_collection  

# Delete all cached searches
cache_collection.delete_many({})  
print("✅ Cleared all cached product data!")









