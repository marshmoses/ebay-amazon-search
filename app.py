#from flask import Flask, request, render_template
#from services.ebay import search_ebay
#from services.database import get_cached_results, cache_results

#app = Flask(__name__)

#@app.route("/")
#def home():
#    return render_template("index.html")

#@app.route("/search")
#def search():
#    query = request.args.get("query")
#    if not query:
#        return render_template("index.html", message="Please enter a search term.")

    # Check MongoDB cache first
#    cached_data = get_cached_results(query)

    # Ensure cached_data is always a list
#    if cached_data is None:
#        cached_data = []

#    if cached_data:
#        return render_template("results.html", query=query, results=cached_data)

#    # Call eBay API if no cached data
#    results = search_ebay(query)

#    if results:
#        cache_results(query, results)  # Store in MongoDB
#        return render_template("results.html", query=query, results=results)
#
#    return render_template("index.html", message="Error fetching data. Try again.")

#if __name__ == "__main__":
#    app.run(debug=True)


import os
from flask import Flask, request, jsonify, render_template
from services.ebay import search_ebay
from services.database import get_cached_results, cache_results, track_product_interaction, get_trending_products
from services.ebay_auth import get_ebay_token
import logging
import traceback
from flask_cors import CORS

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return "Flask App Running on Railway!"  # ✅ Simple response for Railway testing

@app.route("/search", methods=["GET"])
def search():
    """Handles product searches with caching and eBay API calls."""
    query = request.args.get("query", "").strip()

    if not query:
        logging.warning("⚠️ No search term provided.")
        return jsonify({"error": "Please enter a search term."}), 400  

    try:
        # Check if the query is cached
        cached_combined = get_cached_results(query)
        if cached_combined:
            logging.info(f"✅ Cache HIT for query: {query}")
            return jsonify({"results": cached_combined, "query_info": query})

        access_token = get_ebay_token()
        if not access_token:
            logging.error("❌ ERROR: No valid eBay OAuth token found.")
            return jsonify({"error": "eBay authentication failed."}), 500

        # Handle category-based searches
        if "," in query:
            categories = [cat.strip() for cat in query.split(",")]
            all_results = []
            missing_categories = []

            for category in categories:
                if not category:
                    continue
                
                category_results = get_cached_results(category)
                if category_results:
                    logging.info(f"✅ Cache HIT for category: {category}")
                    all_results.extend(category_results)
                else:
                    missing_categories.append(category)

            # Fetch missing categories from eBay API
            for category in missing_categories:
                logging.info(f"🔎 Cache MISS for category: {category}, calling eBay API...")
                category_results = search_ebay(category)
                if category_results:
                    cache_results(category, category_results)
                    all_results.extend(category_results)

            # Remove duplicates
            unique_results = []
            seen_ids = set()
            for item in all_results:
                if item.get("ebay_id") not in seen_ids:
                    seen_ids.add(item.get("ebay_id"))
                    unique_results.append(item)

            # Cache combined results
            if unique_results:
                cache_results(query, unique_results)
                logging.info(f"🔄 Cached combined results for: {query}")
                return jsonify({"results": unique_results})
            else:
                return jsonify({"results": []}), 404

        # Single-category search
        logging.info(f"🔎 Cache MISS for query: {query}, calling eBay API...")
        results = search_ebay(query)
        if results:
            cache_results(query, results)
            logging.info(f"🔄 Cached new results for: {query}")
            return jsonify({"results": results})

        return jsonify({"results": []}), 404

    except Exception as e:
        logging.error(f"❌ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/track-click", methods=["POST"])
def track_click():
    """✅ Tracks product clicks to identify trending items."""
    data = request.json
    product_id = data.get("product_id")
    title = data.get("title")

    if product_id and title:
        track_product_interaction(product_id, title)
        return jsonify({"status": "success"})

    return jsonify({"error": "Missing data"}), 400

@app.route("/trending", methods=["GET"])
def trending():
    """✅ Fetches the trending products based on user searches and clicks."""
    try:
        trending_products = get_trending_products()
        return jsonify({"results": trending_products})
    except Exception as e:
        logging.error(f"❌ ERROR fetching trending products: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # ✅ Get PORT from environment variables
    app.run(debug=False, host="0.0.0.0", port=port)  # ✅ Allow external access
