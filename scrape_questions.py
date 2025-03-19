from playwright.sync_api import sync_playwright
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
STUDYPOOL_SESSION = os.getenv("STUDYPOOL_SESSION")

#  Filtering Criteria
MINIMUM_PRICE = 3.0  
MIN_HOURS = 3  
MIN_DAYS = 1  
MAX_DEADLINE_HOURS = 30 * 24  
RETRY_DELAY = 60  

#  Preferred Categories
PREFERRED_CATEGORIES = {"Business", "Writing", "Science", "Programming", "Mathematics", "Humanities"}

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

    page.reload()

def parse_price(price_text):
    """Convert price string (e.g., '$65.00') to float."""
    return float(price_text.replace("$", "").strip())

def parse_deadline(deadline_text):
    """Convert deadline text (e.g., '10 H', '3 D') to hours."""
    if "H" in deadline_text:
        return int(deadline_text.replace("H", "").strip())
    elif "D" in deadline_text:
        return int(deadline_text.replace("D", "").strip()) * 24
    return 0

def matches_preferred_category(subject):
    """Check if the subject belongs to a preferred category."""
    return any(category.lower() in subject.lower() for category in PREFERRED_CATEGORIES)

def scrape_questions():
    """Continuously scrapes StudyPool until filtered questions are found."""
    while True:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            login_with_cookie(page)

            page.goto("https://www.studypool.com/questions/newest", timeout=60000)

            # Ensure page loads properly
            page.wait_for_selector("#questions-list", timeout=60000)
            page.wait_for_timeout(5000)

            questions_container = page.query_selector("#questions-list")
            question_elements = questions_container.query_selector_all("div.questionBox")

            filtered_questions = []

            for question in question_elements:
                try:
                    title_element = question.query_selector(".questionTitle")
                    subject_element = question.query_selector(".upper-line.category-name")
                    deadline_element = question.query_selector(".timeVal.upper-line")
                    price_element = question.query_selector(".upper-line")
                    link_element = question.query_selector("a[href*='/questions/']")

                    if not (title_element and subject_element and deadline_element and price_element and link_element):
                        continue  

                    title = title_element.inner_text().strip()
                    subject = subject_element.inner_text().strip()
                    deadline_text = deadline_element.inner_text().strip()
                    price_text = price_element.inner_text().strip()
                    question_url = f"https://www.studypool.com{link_element.get_attribute('href')}"

                    price = parse_price(price_text)
                    deadline_hours = parse_deadline(deadline_text)

                    # Correct deadline filtering:
                    
                    if matches_preferred_category(subject) and (MINIMUM_PRICE <= price) and (
                        deadline_hours >= MIN_HOURS or deadline_hours >= MIN_DAYS * 24
                    ):
                        filtered_questions.append({
                            "title": title,
                            "subject": subject,
                            "deadline": deadline_text,
                            "price": price_text,
                            "url": question_url
                        })

                except Exception as e:
                    print(f"⚠ Skipping question due to error: {e}")
                    continue

            browser.close()

            if filtered_questions:
                with open("filtered_questions.json", "w", encoding="utf-8") as file:
                    json.dump(filtered_questions, file, indent=4, ensure_ascii=False)
                print("\n Filtered questions saved to 'filtered_questions.json'!")
                break  

            print(f"⚠ No matching questions found. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    scrape_questions()