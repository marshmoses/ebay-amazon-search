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
        print("🔹 Sample Cached Result:", cached_result["results"][:2])  # Show first 2 results
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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(EBAY_FINDING_API, params=params, headers=headers)
    
    print("🔄 API Request Sent. Status Code:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print("📥 eBay Response:", data)  # Print full response for debugging
        
        items = data.get("findItemsByKeywordsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])

        if not items:
            print("⚠️ No products found.")
            return None

        results = []
        for item in items:
            title = item.get("title", ["N/A"])
            price_info = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
            price = price_info.get("__value__", "N/A")
            currency = price_info.get("@currencyId", "USD")
            condition = item.get("condition", [{}])[0].get("conditionDisplayName", ["N/A"])
            country = item.get("country", ["N/A"])
            image = item.get("galleryURL", ["static/no-image.png"])
            link = item.get("viewItemURL", ["#"])
            rating = item.get("sellerInfo", [{}])[0].get("positiveFeedbackPercent", ["N/A"])

            results.append({
                "title": title[0] if isinstance(title, list) else title,
                "price": f"{price} {currency}",
                "condition": condition[0] if isinstance(condition, list) else condition,
                "country": country[0] if isinstance(country, list) else country,
                "image": image[0] if isinstance(image, list) else image,
                "link": link[0] if isinstance(link, list) else link,
                "rating": f"{rating[0]}%" if isinstance(rating, list) and rating[0] != "N/A" else "No rating"
            })

        # Print sample results
        print("\n🔹 Sample eBay Results:")
        for i, result in enumerate(results[:2]):  # Show first 2 results
            print(f"{i+1}. {result}")

        # Cache results in MongoDB
        cache_collection.insert_one({"query": query, "results": results})
        print("✅ Cached API Response")

        return results
    
    print("❌ API Request Failed. Response:", response.text)
    return None  # Return None if API call fails


search_ebay("Apple Watch")




