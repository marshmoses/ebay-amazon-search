import requests
import base64
import time
import logging
from services.database import db  # Import MongoDB connection

# eBay API Credentials (Replace with yours)
CLIENT_ID = "StephanP-Shopzill-PRD-c40fb8973-06833f8a"
CLIENT_SECRET = "PRD-40fb89735991-da8e-4502-a6d3-0fb8"

# eBay OAuth Token URL
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Access the collection for storing tokens
token_collection = db["ebay_tokens"]

# Configure logging
logging.basicConfig(level=logging.INFO)


def get_ebay_token():
    """Fetch or retrieve eBay OAuth token from MongoDB."""

    try:
        # Check if a valid token exists in MongoDB
        token_data = token_collection.find_one({"_id": "ebay_oauth_token"})

        if not token_data or "access_token" not in token_data:
            logging.warning("⚠️ No eBay token found in MongoDB! Requesting a new one...")
            return request_new_ebay_token()  # Force request if no token exists

        expires_at = token_data.get("expires_at", 0)
        current_time = time.time()

        logging.info(f"🔹 Checking stored token. Expires at: {expires_at}, Current Time: {current_time}")

        if expires_at > current_time:
            logging.info("✅ Using cached eBay token from MongoDB.")
            return token_data["access_token"]  # Return stored token

        logging.warning("⚠️ Token expired. Requesting a new one...")
        return request_new_ebay_token()  # Refresh token if expired

    except Exception as e:
        logging.error(f"❌ ERROR in `get_ebay_token()`: {str(e)}")
        return None


def request_new_ebay_token():
    """Request a new OAuth token from eBay and store it in MongoDB."""

    try:
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }

        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)

        if response.status_code == 200:
            token_info = response.json()
            access_token = token_info.get("access_token")
            expires_in = token_info.get("expires_in", 7200)  # Default to 2 hours if not provided
            expires_at = time.time() + expires_in  # Convert to timestamp

            # Save token in MongoDB
            token_collection.update_one(
                {"_id": "ebay_oauth_token"},
                {"$set": {"access_token": access_token, "expires_at": expires_at}},
                upsert=True
            )

            logging.info("✅ New eBay OAuth token stored in MongoDB.")
            return access_token

        else:
            logging.error(f"❌ ERROR: Failed to get eBay OAuth Token - Status Code: {response.status_code}")
            logging.error(f"🔹 Response: {response.text}")
            return None

    except requests.RequestException as e:
        logging.error(f"❌ ERROR: eBay OAuth request failed: {str(e)}")
        return None


