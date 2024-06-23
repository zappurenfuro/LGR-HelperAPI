from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import re
import time

app = Flask(__name__)

def scrape_latest_posts(url):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome"

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)

    try:
        driver.get(url)
        print(f"Loaded URL: {driver.current_url}")

        wait = WebDriverWait(driver, 20)
        try:
            articles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article')))
            latest_posts = []

            for article in articles[:5]:
                try:
                    title_element = article.find_element(By.CSS_SELECTOR, 'span.notice-subject')
                    date_element = article.find_element(By.CSS_SELECTOR, 'span.notice-date')
                    title = title_element.text
                    date = date_element.text

                    # Click to get the content
                    title_element.click()
                    time.sleep(2)  # Wait for the content to load

                    content_element = article.find_element(By.CSS_SELECTOR, 'div.answer')
                    content = content_element.get_attribute('innerHTML')

                    latest_posts.append({
                        'title': title,
                        'date': date,
                        'content': content
                    })

                except NoSuchElementException:
                    print("Element not found, skipping article.")
                    continue
                except StaleElementReferenceException:
                    print("Stale element reference, skipping article.")
                    continue

            # Filter posts to only include those with dates in the title
            filtered_posts = [post for post in latest_posts if re.search(r'\[\d{6,8}', post['title'])]

            return filtered_posts

        except TimeoutException:
            print("Timeout waiting for posts")
            return None

    finally:
        driver.quit()

@app.route('/latest_posts', methods=['GET'])
def get_latest_posts():
    url = 'https://notice2.line.me/LGGRTH/android/document/notice'
    result = scrape_latest_posts(url)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to scrape the latest posts"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
