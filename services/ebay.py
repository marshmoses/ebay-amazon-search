import requests
from services.database import cache_collection

# eBay API Details
APP_ID = "MosesMac-pricemon-PRD-85bb4ae7d-e6d9b5f3"
EBAY_FINDING_API = "https://svcs.ebay.com/services/search/FindingService/v1"

def search_ebay(query):
    """Search for products on eBay and return results with caching."""
    
    # Check if query is already cached
    cached_result = cache_collection.find_one({"query": query})
    if cached_result:
        print("✅ Using Cached Data")
        return cached_result["results"]

    # API request
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "paginationInput.entriesPerPage": 5,
        "outputSelector": "PictureURLLarge"
    }

    response = requests.get(EBAY_FINDING_API, params=params)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("findItemsByKeywordsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])

        results = []
        for item in items:
            title = item.get("title", ["N/A"])[0]
            price = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "N/A")
            currency = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", "USD")
            condition = item.get("condition", [{}])[0].get("conditionDisplayName", ["N/A"])[0]
            country = item.get("country", ["N/A"])[0]
            image = item.get("galleryURL", ["static/no-image.png"])[0]
            link = item.get("viewItemURL", ["#"])[0]
            rating = item.get("sellerInfo", [{}])[0].get("positiveFeedbackPercent", ["N/A"])[0]

            results.append({
                "title": title,
                "price": f"{price} {currency}",
                "condition": condition,
                "country": country,
                "image": image,
                "link": link,
                "rating": f"{rating}%" if rating != "N/A" else "No rating"
            })

        # Cache results in MongoDB
        cache_collection.insert_one({"query": query, "results": results})
        print("✅ Cached API Response")

        return results
    
    return None  # Return None if API call fails
