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

from flask import Flask, request, render_template, jsonify
from services.ebay import search_ebay
from services.database import get_cached_results, cache_results
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return render_template("search.html")

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()

    if not query:
        return render_template("search.html", message="Please enter a search term.")

    # Check MongoDB cache first
    cached_data = get_cached_results(query) or []

    if cached_data:
        logging.info(f"✅ Cache hit for query: {query}")
        return render_template("results.html", query=query, results=cached_data)

    # Call eBay API if no cached data
    results = search_ebay(query)

    if results:
        cache_results(query, results)
        logging.info(f"🔄 Cached new results for query: {query}")
        return render_template("results.html", query=query, results=results)

    logging.error(f"❌ Failed to fetch data for query: {query}")
    return render_template("search.html", message="Error fetching data. Try again later.")

if __name__ == "__main__":
    app.run(debug=True)
