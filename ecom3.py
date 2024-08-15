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

# Configure logging
logging.basicConfig(
    filename='SpeedHobby_Scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SpeedHobby_Scraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("Initialized WebDriver")

    def extract_product_links(self, url, output_file):
        def extract_links_from_page(url):
            self.driver.get(url)
            time.sleep(5)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.product-index .prod-image a')
            product_links = [element.get_attribute('href') for element in product_elements if element.get_attribute('href')]

            with open(output_file, "a", newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Product Link'])
                if csvfile.tell() == 0:
                    writer.writeheader()
                for link in product_links:
                    writer.writerow({'Product Link': link})

            logging.info(f"Extracted {len(product_links)} product links from {url}")
            return product_links

        def get_next_page_url():
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, '#pagination .next-page')
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
            logging.info(f"Total product links extracted: {len(all_links)}")
            return all_links

        extract_all_product_links(url)

    def extract_product_details(self,product_urls_file, output_file):
        def extract_details(product_url):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            for attempt in range(2):  
                try:
                    response = requests.get(product_url, headers=headers)
                    response.raise_for_status() 

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract JSON data embedded in a <script> tag
                    script_element = soup.find('script', {'class': 'product-json'})
                    if script_element:
                        product_json = script_element.string
                        product_data = json.loads(product_json)

                        details = []
                        for variant in product_data['variants']:
                            formatted_price = "{:,.2f}".format(float(variant['price']) / 100)
                            details.append({
                                'Title': product_data['title'],
                                'Brand': product_data['vendor'],
                                'Variants': variant['title'],
                                'SKU': variant['sku'],
                                'Price': f"Rs. {formatted_price}",
                                'Stock Status': 'In Stock' if variant['available'] else 'Out of Stock',
                                'Quantity': variant['inventory_quantity'],
                                'URL': product_url
                            })
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
                            'Quantity': 'N/A',
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
                'Quantity': 'N/A',
                'URL': product_url
            }]

        with open(product_urls_file, "r") as file:
            reader = csv.DictReader(file)
            product_urls = [row['Product Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Brand', 'Variants', 'SKU', 'Price', 'Stock Status', 'Quantity', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for url in product_urls:
                product_details_list = extract_details(url)
                for product_details in product_details_list:
                    writer.writerow(product_details)
            
            logging.info(f"Product details extracted and saved to {output_file}")
    def close_driver(self):
        self.driver.quit()
        logging.info("WebDriver closed")

if __name__ == "__main__":
    scraper = SpeedHobby_Scraper()
    
    url = 'https://www.speedhobby.dk/collections/all'
    product_urls = "speedhobby_product_urls.csv"
    product_details = "speedhobby_product_details.csv"
    
    print("Choose an option:")
    print("1. Extract product links from collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2): ")

    if option == "1":
        scraper.extract_product_links(url, product_urls)
        scraper.close_driver()
    elif option == "2":
        scraper.close_driver()
        scraper.extract_product_details(product_urls, product_details)
        
    else:
        print("Invalid option. Please run the script again and choose a valid option.")
        scraper.close_driver()
