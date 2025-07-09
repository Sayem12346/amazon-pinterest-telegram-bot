import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv
import time

load_dotenv()
EMAIL = os.getenv("PINTEREST_EMAIL")
PASSWORD = os.getenv("PINTEREST_PASSWORD")
BOARD_NAME = os.getenv("BOARD_NAME")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def scrape_amazon_product(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    title_tag = soup.select_one("#productTitle")
    image_tag = soup.select_one("#imgTagWrapperId img")
    desc_tag = soup.select_one("#feature-bullets")

    if not title_tag or not image_tag:
        raise Exception("Product info not found. Check the link.")

    title = title_tag.get_text(strip=True)
    image = image_tag['src']
    description = desc_tag.get_text(strip=True) if desc_tag else "No description available."

    return title, image, description

def post_to_pinterest(title, image_url, description):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.pinterest.com/login")

    time.sleep(3)
    driver.find_element(By.NAME, "id").send_keys(EMAIL)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)

    driver.get("https://www.pinterest.com/pin-builder/")
    time.sleep(3)

    img_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    img_data = requests.get(image_url).content
    with open("temp.jpg", "wb") as f:
        f.write(img_data)

    img_input.send_keys(os.path.abspath("temp.jpg"))
    time.sleep(2)

    title_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder='Add your title']")
    desc_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder='Tell everyone what your Pin is about']")
    title_input.send_keys(title)
    desc_input.send_keys(description)

    board_dropdown = driver.find_element(By.XPATH, f"//div[text()='{BOARD_NAME}']")
    board_dropdown.click()
    time.sleep(1)

    publish_btn = driver.find_element(By.XPATH, "//div[text()='Publish']")
    publish_btn.click()
    time.sleep(3)

    driver.quit()

def start(update, context):
    update.message.reply_text('👋 আমাজন লিংক দিন, আমি Pinterest-এ পোস্ট করে দিবো।')

def handle_message(update, context):
    url = update.message.text
    update.message.reply_text("🔍 লিংক প্রসেস করা হচ্ছে...")
    try:
        title, image, description = scrape_amazon_product(url)
        post_to_pinterest(title, image, description)
        update.message.reply_text("✅ Pinterest-এ সফলভাবে পোস্ট হয়েছে!")
    except Exception as e:
        update.message.reply_text(f"❌ সমস্যা হয়েছে: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
