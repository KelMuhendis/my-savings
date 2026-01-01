import os
from datetime import datetime, timedelta
import time
import json
import math
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def get_data():
    file_path = "currencies.json"
    if not os.path.exists(file_path):
        data = {
                "timestamp": datetime(2000, 1, 1).isoformat()
            }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    timestamp_str = data.get("timestamp")
    timestamp = datetime.fromisoformat(timestamp_str)

    one_hour_ago = datetime.now() - timedelta(hours=1)

    if timestamp <= one_hour_ago:
        print("Currency ratings need to be updated.")
        url_market = "https://www.altinkaynak.com/canli-kurlar/"
        url_bank = "https://www.yapikredi.com.tr/yatirimci-kosesi/altin-bilgileri"
        scraped_data = []

        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        print("Starting browser...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            print(f"Loading {url_market}...")
            driver.get(url_market)
            time.sleep(5) 

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            def extract_from_table(keyword):
                target_table = None
                for table in soup.find_all("table", class_="table"):
                    headers = [th.get_text(strip=True) for th in table.find_all("th")]
                    if keyword in headers:
                        target_table = table
                        break
                
                if target_table:
                    tbody = target_table.find("tbody")
                    if tbody:
                        rows = tbody.find_all("tr")
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) >= 3:
                                name = cols[0].get_text(strip=True)
                                buy = cols[1].get_text(strip=True)
                                scraped_data.append((name, buy))

            extract_from_table("Döviz")
            extract_from_table("Altın")

            print(f"Loading {url_bank}...")
            driver.get(url_bank)
            time.sleep(5) 
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            value = soup.select_one("#leftBoxResult span").text.strip().replace("  TL", "").strip()

            scraped_data.append(("Banka Altın", value))

            data = {
                "timestamp": datetime.now().isoformat(), 
                "price": [
                {"name": name, "value": value}
                    for name, value in scraped_data
                ]
            }
            with open("currencies.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return data.get("price") 
        except Exception as e:
            print(f"Scraping error: {e}")
            return []
        finally:
            driver.quit()
    else:
        return data.get("price") 

def calculate_final_savings(currencies, savings):
    def tr_number_to_float(value: str) -> float:
        return float(value.replace('.', '').replace(',', '.'))

    price_dict = {
        item["name"]: tr_number_to_float(item["value"])
        for item in currencies
    }

    total = 0.0

    for item in savings.get("saving", []):
        asset = item["name"]
        amount = item["amount"]
        if asset in price_dict:
            total += amount * price_dict[asset]

    return total

if __name__ == "__main__":
    currencies = get_data()
    with open("savings.json", encoding="utf-8") as f:
        savings = json.load(f)
    total_savings = math.floor(calculate_final_savings(currencies, savings))
    money = math.floor(total_savings)
    print(f"₺{total_savings:,}")