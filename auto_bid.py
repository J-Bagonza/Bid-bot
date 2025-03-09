from playwright.sync_api import sync_playwright
import json
import os
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
STUDYPOOL_SESSION = os.getenv("STUDYPOOL_SESSION")

# ✅ Define bidding ranges
BID_PRICE_RANGE = (5, 1000)  # ✅ Min and max bid price
DELIVERY_TIME_RANGE = (5, 360)  # ✅ Min and max delivery time
MAX_BIDS = 5  # ✅ Set how many bids the bot should place per run

def login_with_cookie(page):
    """Load StudyPool session using stored cookie."""
    page.goto("https://www.studypool.com", timeout=90000, wait_until="domcontentloaded")
    
    page.context.add_cookies([{
        "name": "PHPSESSID",
        "value": STUDYPOOL_SESSION,
        "domain": "www.studypool.com",
        "path": "/",
        "secure": True,
        "httpOnly": True
    }])

    page.reload()  # Refresh page to apply the cookie

def place_bid(page, question_url):
    """Automate the bidding process for a single question."""
    print(f"🚀 Opening question: {question_url}")
    page.goto(question_url, timeout=60000)

    # ✅ Wait for bid elements to load
    page.wait_for_timeout(3000)  # Allow time for dynamic elements to load

    # ✅ Generate random bid price and delivery time
    bid_price = random.randint(*BID_PRICE_RANGE)
    delivery_time = random.randint(*DELIVERY_TIME_RANGE)

    print(f"💰 Bidding ${bid_price} | ⏳ Delivery in {delivery_time} hours")

    # ✅ Click the outer dropdown container to activate the price selection
    price_dropdown_container = page.query_selector("#s2id_priceDropDown")
    if price_dropdown_container:
        price_dropdown_container.click()
        page.wait_for_timeout(1000)  # Wait for dropdown to open

    # ✅ Select the bid price in the actual dropdown
    price_dropdown = page.query_selector("#priceDropDown")
    if price_dropdown:
        price_dropdown.select_option(str(bid_price))
    else:
        print("⚠ Could not find price dropdown.")
        return False  

    # ✅ Enter delivery time
    delivery_input = page.query_selector("#deliver_in")
    if delivery_input:
        delivery_input.fill(str(delivery_time))  
    else:
        print("⚠ Could not find delivery time input.")
        return False

    # ✅ Click the finalize bid checkbox
    finalize_checkbox = page.query_selector(".finalize-bid-description")
    if finalize_checkbox:
        finalize_checkbox.click()
    else:
        print("⚠ Could not find finalize checkbox.")
        return False

    # ✅ Click "Place Bid" button
    place_bid_button = page.query_selector("#placeABidButton")
    if place_bid_button:
        place_bid_button.click()
        print("✅ Bid placed successfully!")
        return True
    else:
        print("⚠ Could not find 'Place Bid' button.")
        return False

def auto_bid():
    """Reads filtered questions and places bids."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  
        page = browser.new_page()

        login_with_cookie(page)

        # ✅ Read filtered questions
        if not os.path.exists("filtered_questions.json"):
            print("⚠ No filtered questions found!")
            return

        with open("filtered_questions.json", "r", encoding="utf-8") as file:
            questions = json.load(file)

        if not questions:
            print("⚠ No questions available to bid on.")
            return

        bids_placed = 0
        for question in questions:
            if bids_placed >= MAX_BIDS:
                print("✅ Reached max bid limit.")
                break  

            question_url = question.get("url")
            if not question_url:
                print(f"⚠ Skipping {question['title']} (No URL found)")
                continue  

            success = place_bid(page, question_url)
            if success:
                bids_placed += 1

        browser.close()
        print(f"\n✅ Bidding process completed! {bids_placed} bids placed.")

if __name__ == "__main__":
    auto_bid()