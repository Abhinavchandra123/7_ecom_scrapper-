import csv
import json
import logging
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging for RcklubbenScraper
logging.basicConfig(
    filename='RcklubbenScraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RcklubbenScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_product_links(self, url, output_file):
        def extract_links_from_page(url):
            self.driver.get(url)
            time.sleep(5)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.block.product.size-medium.fixed-ratio .main .img-link')
            product_links = [element.get_attribute('href') for element in product_elements if element.get_attribute('href')]

            with open(output_file, "a", newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Product Link'])
                if csvfile.tell() == 0: 
                    writer.writeheader()
                for link in product_links:
                    writer.writerow({'Product Link': link})

            logging.info(f"Extracted {len(product_links)} product links.")
            return product_links

        def get_next_page_url():
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, '.pagination .next')
                return next_button.get_attribute('href')
            except:
                return None

        def extract_all_product_links(start_url):
            all_links = []
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
            return all_links

        extract_all_product_links(url)

    def extract_product_details(self,product_urls_file, output_file):
        def extract_details(product_url):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # Try to fetch and parse the product details
            for attempt in range(2):  # Try up to 2 times
                try:
                    response = requests.get(product_url, headers=headers)
                    response.raise_for_status()  # Check for request errors

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract JSON data embedded in a <script> tag
                    script_element = soup.find('script', {'id': lambda x: x and 'ProductJson-' in x})
                    if script_element:
                        product_json = script_element.string
                        product_data = json.loads(product_json)

                        details = []
                        for variant in product_data['variants']:
                            details.append({
                                'Title': product_data['title'],
                                'Brand': product_data['vendor'],
                                'Variants': variant['title'],
                                'SKU': variant['sku'],
                                'Price': f"Rs. {variant['price'] / 100:.2f}",  # Formatting price
                                'Stock Status': 'In Stock' if variant['available'] else 'Out of Stock',
                                'URL': product_url
                            })
                        logging.info(f"Extracted details for {product_url}.")
                        return details
                    else:
                        logging.error(f'No product JSON found at {product_url}')
                        return [{
                            'Title': 'N/A',
                            'Brand': 'N/A',
                            'Variants': 'N/A',
                            'SKU': 'N/A',
                            'Price': 'N/A',
                            'Stock Status': 'N/A',
                            'URL': product_url
                        }]

                except Exception as e:
                    logging.error(f'Error extracting details from {product_url} on attempt {attempt+1}: {e}')
                    if attempt == 0:  # Wait before retrying only after the first attempt
                        time.sleep(20)

            # If all attempts fail
            logging.error(f'Failed to extract details from {product_url} after multiple attempts.')
            return [{
                'Title': 'N/A',
                'Brand': 'N/A',
                'Variants': 'N/A',
                'SKU': 'N/A',
                'Price': 'N/A',
                'Stock Status': 'N/A',
                'URL': product_url
            }]

        with open(product_urls_file, "r") as file:
            reader = csv.DictReader(file)
            product_urls = [row['Product Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Brand', 'Variants', 'SKU', 'Price', 'Stock Status', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url in product_urls:
                product_details = extract_details(url)
                for detail in product_details:
                    writer.writerow(detail)
            logging.info(f"Product details extracted and saved to {output_file}")

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = RcklubbenScraper()
    
    url = 'https://rcklubben.dk/collections/all'
    product_urls = "rcklubben_product_urls.csv"
    product_details = "rcklubben_product_details.csv"
    scraper.extract_product_links(url, product_urls)
    scraper.close_driver()
    scraper.extract_product_details(product_urls, product_details)
    # print("Choose an option:")
    # print("1. Extract product links from collection links")
    # print("2. Extract product details from product links")
    # option = input("Enter the option number (1, 2): ")

    # if option == "1":
    #     print("Extracting product links...")
    #     scraper.extract_product_links(url, product_urls)
    #     scraper.close_driver()
    # elif option == "2":
    #     print("Extracting product details...")
    #     scraper.close_driver()
    #     scraper.extract_product_details(product_urls, product_details)
    # else:
    #     print("Invalid option. Please run the script again and choose a valid option.")
    #     scraper.close_driver()

    
    print("RcklubbenScraper execution completed.")
    
