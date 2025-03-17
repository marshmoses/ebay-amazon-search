import requests
import logging
import datetime
import time
from services.database import cache_collection, store_user_search
from services.ebay_auth import get_ebay_token  # Import OAuth token function

CACHE_EXPIRATION_HOURS = 24  # Cache expiration time
EBAY_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
MAX_RETRIES = 3  # Number of times to retry
TIMEOUT = 20  # API request timeout in seconds


def search_ebay(query, max_results=50):
    """Search for products on eBay using OAuth authentication from MongoDB."""
    
    access_token = get_ebay_token()  # Retrieve token from MongoDB

    if not access_token:
        logging.error("❌ ERROR: Unable to get a valid eBay token.")
        return []

    # Check MongoDB for cached results
    cached_result = cache_collection.find_one({"query": query})
    
    if cached_result:
        last_updated = cached_result.get("last_updated", datetime.datetime.min)
        time_difference = datetime.datetime.utcnow() - last_updated

        if time_difference.total_seconds() < CACHE_EXPIRATION_HOURS * 3600:
            logging.info(f"📦 Returning cached eBay results for query: {query}")
            return cached_result["results"]

    results = []
    page = 1
    total_results = 0

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-EBAY-C-ENDUSERCTX": "contextualLocation=country=US"
            }

            params = {
                "q": query,
                "limit": min(50, max_results - total_results)
            }

            logging.info(f"🔎 Attempt {attempt + 1}: Fetching page {page} for query: {query}")
            response = requests.get(EBAY_API_URL, headers=headers, params=params, timeout=TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                items = data.get("itemSummaries", [])

                if not items:
                    logging.warning(f"⚠️ No results found for query: {query}")
                    return []

                # Process and return results
                for item in items:
                    try:
                        results.append({
                            "ebay_id": item.get("itemId", "N/A"),
                            "title": item.get("title", "N/A"),
                            "price": f"{item.get('price', {}).get('value', 'N/A')} {item.get('price', {}).get('currency', 'USD')}",
                            "condition": item.get("condition", "N/A"),
                            "image": item.get("thumbnailImages", [{}])[0].get("imageUrl", "static/no-image.png"),
                            "link": item.get("itemWebUrl", "#"),
                            "rating": item.get("seller", {}).get("feedbackPercentage", "No rating") + "%"
                        })
                    except Exception as e:
                        logging.warning(f"⚠️ Error processing item: {e}", exc_info=True)

                total_results += len(items)
                page += 1

                if len(items) == 0:
                    break

                logging.info(f"✅ Retrieved {total_results} eBay items for '{query}'")

                # Store results in MongoDB (cache)
                cache_collection.update_one(
                    {"query": query},
                    {"$set": {"results": results, "last_updated": datetime.datetime.utcnow()}},
                    upsert=True
                )

                # Store user searches for trending tracking
                store_user_search(query, results[:6])

                return results

            elif response.status_code == 429:
                logging.warning("⚠️ Rate limit exceeded. Retrying after 10 seconds...")
                time.sleep(10)  # Wait before retrying

            else:
                logging.error(f"❌ eBay API Error {response.status_code}: {response.text}")
                break  # Stop retries if other errors occur

        except requests.exceptions.Timeout:
            logging.warning(f"⚠️ Timeout occurred for query: {query}. Retrying...")
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Request failed: {str(e)}")
            break

        attempt += 1

    logging.error(f"❌ Failed to fetch data for query: {query} after {MAX_RETRIES} attempts.")
    return []




