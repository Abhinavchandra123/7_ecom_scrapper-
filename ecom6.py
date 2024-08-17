import csv
import gc
import json
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging for ModelSportScraper
logging.basicConfig(
    filename='ModelSportScraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ModelSportScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--single-process")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=800x600")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # self.driver.set_window_size(1920, 1080)
        
        self.driver.get("https://modelsport.dk/")
        time.sleep(4)
        # self.save_cookies("modelsport_cookies.json") # use when needed to refresh cookies or when cookies file missing
        self.load_cookies("modelsport_cookies.json")
        self.driver.refresh()
        logging.info("Initialized ModelSportScraper and loaded cookies.")

    def save_cookies(self, path):
        with open(path, 'w') as file:
            json.dump(self.driver.get_cookies(), file)
        logging.info(f"Cookies saved to {path}.")

    def load_cookies(self, path):
        try:
            with open(path, 'r') as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            logging.info(f"Cookies loaded from {path}.")
        except FileNotFoundError:
            logging.error(f"Cookies file {path} not found.")
        except json.JSONDecodeError:
            logging.error(f"Error decoding cookies from {path}.")

    def extract_collection_links(self, output_file, url):
        all_links = []
        self.driver.get(url)
        time.sleep(2)

        wait = WebDriverWait(self.driver, 10)
        menu = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.menu.productmenu.menu-inline")))

        collection_links = menu.find_elements(By.TAG_NAME, "a")
        
        for link in collection_links:
            href = link.get_attribute("href")
            if href and "shop" in href:
                all_links.append(href)

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for link in all_links:
                writer.writerow([link])
        
        logging.info(f"Extracted {len(all_links)} collection links.")

    def get_product_links(self, output_file):
        product_links = []
        sitemap_url = "https://modelsport.dk/sitemap/produkter/"
        self.driver.get(sitemap_url)
        time.sleep(3)  # Allow the page to fully load
        page_count = 1

        while True:
            try:
                logging.info(f"Processing page {page_count}...")

                # Find all product links within the specified <ul> element
                product_list = self.driver.find_element(By.CSS_SELECTOR, '.m-sitemap-prod.m-links.list-unstyled')
                product_items = product_list.find_elements(By.CSS_SELECTOR, 'li.m-sitemap-prod-item.m-links-prod a')
                
                page_links = [item.get_attribute('href') for item in product_items]
                product_links.extend(page_links)

                logging.info(f"Extracted {len(page_links)} product links from page {page_count}.")
                # Check if there is a "next" button and click it
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, '.w-pagination-list a[rel="next"]')
                    if next_button:
                        next_button.click()
                        time.sleep(3)  # Wait for the next page to load
                        page_count += 1
                    else:
                        break  # Exit the loop if there is no "next" button
                except Exception as a:
                    logging.error(f"Error occurred on page {page_count}: cant find next button")
                    break

            except Exception as e:
                logging.error(f"Error occurred on page {page_count}: {str(e)}")
                break

        # Save the extracted links to the output file
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for link in product_links:
                writer.writerow([link])

        logging.info(f"Total of {len(product_links)} product links extracted.")

    def extract_product_details(self, product_urls, output_file, batch_size=500):
        # Delete the file if it already exists
        if os.path.exists(output_file):
            os.remove(output_file)

        # Read product URLs from file
        with open(product_urls, 'r') as file:
            product_urls = [line.strip() for line in file]

        # Open output file in append mode to save batch results
        with open(output_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Only write the header if the file is empty
            if file.tell() == 0:
                writer.writerow(['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'URL'])

            # Process URLs in batches
            for i in range(0, len(product_urls), batch_size):
                batch_urls = product_urls[i:i + batch_size]
                self.process_batch(batch_urls, writer)
                gc.collect()  # Force garbage collection after each batch

    def process_batch(self, batch_urls, writer):
        for url in batch_urls:
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'zoomHook')))
            try:
                title = self.get_element_text(By.CSS_SELECTOR, 'h1.m-product-title.product-title', default="N/A")
                brand = self.get_element_attribute(By.CSS_SELECTOR, 'p.m-product-brand a.m-product-brand-link', 'title', default="N/A").split(': ')[-1]
                base_price = self.get_element_attribute(By.CSS_SELECTOR, 'meta[itemprop="price"]', 'content', default="N/A")
                sku = self.get_element_text(By.CSS_SELECTOR, 'span.m-product-itemNumber-value', default="N/A")
                stock_status = self.get_stock_status(By.CSS_SELECTOR, 'span.m-product-stock-text')

                variants = self.driver.find_elements(By.CSS_SELECTOR, 'div.m-product-buttons-list-button.data')
                if variants:
                    for variant in variants:
                        variant.find_element(By.TAG_NAME, 'label').click()
                        time.sleep(1)  # Adjust or remove sleep
                        variant_price = self.get_element_text(By.CSS_SELECTOR, 'span.selected-priceLine .price', default="N/A")
                        variant_sku = self.get_element_text(By.CSS_SELECTOR, 'span.product-itemNumber-value.selected-itemNumber-value', default="N/A")
                        variant_stock_status = self.get_stock_status(By.CSS_SELECTOR, 'span.product-stock-text.selected-stock-text')
                        writer.writerow([title, brand, variant_sku, variant_price, variant_stock_status, url])
                else:
                    writer.writerow([title, brand, sku, base_price, stock_status, url])

            except Exception as e:
                logging.error(f"Error extracting details for {url}: {e}")
                continue

    # Helper functions for element extraction
    def get_element_text(self, by, selector, default=""):
        try:
            return self.driver.find_element(by, selector).text
        except Exception:
            return default

    def get_element_attribute(self, by, selector, attribute, default=""):
        try:
            return self.driver.find_element(by, selector).get_attribute(attribute)
        except Exception:
            return default

    def get_stock_status(self, by, selector):
        try:
            stock_text = self.driver.find_element(by, selector).text
            if "Ikke på lager" in stock_text:
                return "Out of Stock"
            elif "På Lager" in stock_text:
                return "In Stock"
            else:
                return "N/A"
        except Exception:
            return "N/A"
    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ModelSportScraper()
    
    url = "https://modelsport.dk/"
    output_file = 'modelsport_collections.csv'
    product_urls = "modelsport_urls.csv"
    product_details = "modelsport_details.csv"
    
    print("Choose an option:")
    print("1. Extract product links and product details")
    print("2. Extract product links")
    print("3. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")

    if option == "1":
        scraper.get_product_links(output_file)
        scraper.extract_product_details(output_file, product_details)
    elif option == "2":
        scraper.get_product_links(output_file)
    elif option == "3":
        scraper.extract_product_details(output_file, product_details)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
    print("ModelSportScraper execution completed.")
