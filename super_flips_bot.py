import time
import os
import requests
import schedule
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from telegram import Bot

TELEGRAM_TOKEN = '8199786673:AAH9rM4L-enn0TCMZXeTaMqNEfEeJx3MDSs'
CHAT_ID = '6853246366'
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'

SEEN_OFFERUP = set()
SEEN_CRAIGSLIST = set()
SEEN_FB = set()

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def check_facebook():
    print("🌐 Запуск парсинга Facebook...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--user-data-dir=/tmp/selenium_fb")

    try:
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.facebook.com/marketplace/sandiego/vehicles?sellerType=individual&exact=false")
        time.sleep(10)
        posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/marketplace/item/")]')
        print(f"🔍 Facebook: найдено {len(posts)} постов")

        bot = Bot(token=TELEGRAM_TOKEN)

        for post in posts[:5]:
            title = post.text.split("\n")[0]
            url = post.get_attribute("href")
            if url not in SEEN_FB:
                SEEN_FB.add(url)
                msg = f"🚗 {title}\n{url}"
                print("📤 [Facebook] Отправка:", msg)
                bot.send_message(chat_id=CHAT_ID, text=msg)
        driver.quit()
    except Exception as e:
        print("❌ Facebook ошибка:", e)

def check_offerup():
    print("🌐 Запуск парсинга OfferUp...")
    urls = [
        'https://offerup.com/explore/sck/ca/san_diego/cars-trucks',
        'https://offerup.com/explore/sck/ca/el_cajon/cars-trucks'
    ]
    bot = Bot(token=TELEGRAM_TOKEN)

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(r.text, 'html.parser')
            cards = soup.select('a[href^="/item/detail/"]')
            print(f"🔍 OfferUp: найдено {len(cards)} карточек на {url}")
            for card in cards:
                link = "https://offerup.com" + card['href'].split('?')[0]
                title = card.get('title') or 'Объявление'
                if link not in SEEN_OFFERUP:
                    SEEN_OFFERUP.add(link)
                    msg = f"🚘 {title}\n{link}"
                    print("📤 [OfferUp] Отправка:", msg)
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    break
        except Exception as e:
            print("❌ OfferUp ошибка:", e)

def check_craigslist():
    print("🌐 Запуск парсинга Craigslist...")
    url = 'https://sandiego.craigslist.org/search/cta?postal=92122&purveyor=owner&search_distance=100'
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, 'html.parser')
        posts = soup.select('.result-info')
        print(f"🔍 Craigslist: найдено {len(posts)} постов")
        for post in posts[:5]:
            title = post.select_one('.result-title').text.strip()
            link = post.select_one('.result-title')['href']
            price_tag = post.select_one('.result-price')
            price = price_tag.text.strip() if price_tag else 'No price'
            if link not in SEEN_CRAIGSLIST:
                SEEN_CRAIGSLIST.add(link)
                msg = f"🛻 {title} - {price}\n{link}"
                print("📤 [Craigslist] Отправка:", msg)
                bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print("❌ Craigslist ошибка:", e)

schedule.every(2).minutes.do(check_facebook)
schedule.every(3).minutes.do(check_offerup)
schedule.every(4).minutes.do(check_craigslist)

print("✅ Super Flips Docker Bot запущен!")

if __name__ == '__main__':
    print("🔥 Вошли в __main__")
    check_facebook()
    check_offerup()
    check_craigslist()
    while True:
        schedule.run_pending()
        time.sleep(10)