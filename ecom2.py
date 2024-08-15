import csv
import json
import os
import re
import requests
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging
logging.basicConfig(
    filename='MorfarsScraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MorfarsScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("Initialized WebDriver")

    def extract_product_links(self, url, output_file):
        def extract_links_from_page(url):
            self.driver.get(url)
            time.sleep(5)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.product-card__figure a')
            product_links = [element.get_attribute('href') for element in product_elements if element.get_attribute('href')]

            with open(output_file, "a", newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Product Link'])
                if csvfile.tell() == 0:  # Check if the file is empty to write the header
                    writer.writeheader()
                for link in product_links:
                    writer.writerow({'Product Link': link})
            
            logging.info(f"Extracted {len(product_links)} product links from {url}")
            return product_links

        def get_next_page_url():
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, '.pagination__item[rel="next"]')
                if "pagination__item--disabled" in next_button.get_attribute("class"):
                    return None
                return next_button.get_attribute('href')
            except:
                return None

        def extract_all_product_links(start_url):
            all_links = []
            
            # Check if the output file exists and delete it
            if os.path.exists(output_file):
                os.remove(output_file)
            
            self.driver.get(start_url)
            while True:
                product_links = extract_links_from_page(self.driver.current_url)
                all_links.extend(product_links)
                next_page_url = get_next_page_url()
                if next_page_url:
                    self.driver.get(next_page_url)
                    time.sleep(5)
                else:
                    break
            logging.info(f"Total product links extracted: {len(all_links)}")
            return all_links

        extract_all_product_links(url)
        
    def extract_product_details(self, product_urls_file, output_file):
        def extract_details(product_url):
            json_url = product_url + ".json"
            response = requests.get(json_url)
            if response.status_code == 200:
                product_data = response.json()['product']
                variants = product_data['variants']

                details = []
                for variant in variants:
                    title = product_data.get('title', 'N/A')
                    brand = product_data.get('vendor', 'N/A')
                    sku = variant.get('sku', 'N/A')
                    available = 'In Stock' if variant.get('inventory_management', 'shopify') == 'shopify' else 'Out of Stock'
                    price = variant.get('price', 'N/A')
                    quantity = variant.get('inventory_quantity', 'N/A')

                    if quantity == 'N/A' or int(quantity) <= 0:
                        try:
                            self.driver.get(product_url)
                        except:
                            time.sleep(5)
                            self.driver.refresh()
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info__inventory .text-with-icon'))
                            )
                            stock_status_element = self.driver.find_element(By.CSS_SELECTOR, '.product-info__inventory .text-with-icon')
                            stock_status = stock_status_element.text if stock_status_element else 'N/A'
                        except:
                            try:
                                sold_out_badge = self.driver.find_element(By.CSS_SELECTOR, '.badge--sold-out')
                                if sold_out_badge.is_displayed():
                                    stock_status = sold_out_badge.text
                                else:
                                    stock_status = 'N/A'
                            except:
                                stock_status = 'N/A'
                        if stock_status in ['UDSOLGT', 'Udsolgt']:
                            available = 'Out of Stock'
                        else:
                            available = 'In Stock'
                        
                    details.append({
                        'Title': title,
                        'Brand': brand,
                        'SKU': sku,
                        'Price': f'{price} kr' if price != 'N/A' else 'N/A',
                        'Stock Status': available,
                        'Quantity': quantity,
                        'URL': product_url
                    })
                return details
            else:
                logging.error(f"Failed to fetch data from {json_url}")
                return [{
                    'Title': 'N/A',
                    'Brand': 'N/A',
                    'SKU': 'N/A',
                    'Price': 'N/A',
                    'Stock Status': 'N/A',
                    'Quantity': 'N/A',
                    'URL': product_url
                }]

        with open(product_urls_file, "r") as file:
            reader = csv.DictReader(file)
            product_urls = [row['Product Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'Quantity', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url in product_urls:
                try:
                    product_details_list = extract_details(url)
                    for product_details in product_details_list:
                        writer.writerow(product_details)
                except:
                    try:
                        time.sleep(30)
                        product_details_list = extract_details(url)
                        for product_details in product_details_list:
                            writer.writerow(product_details)
                    except Exception as a:
                        logging.info(f"error while processing url: {url} \n error:{a}")
            logging.info(f"Product details extracted and saved to {output_file}")

    def close_driver(self):
        self.driver.quit()
        logging.info("WebDriver closed")

if __name__ == "__main__":
    scraper = MorfarsScraper()
    
    url = 'https://morfars.dk/collections/all'
    product_urls = "morfars_product_urls.csv"
    product_details = "morfars_product_details.csv"
    
    print("Choose an option:")
    print("1. Extract product links from collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2): ")

    if option == "1":
        scraper.extract_product_links(url, product_urls)
    elif option == "2":
        scraper.extract_product_details(product_urls, product_details)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
