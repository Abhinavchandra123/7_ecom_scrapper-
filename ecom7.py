import csv
import gc
import json
import logging
import os
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

logging.basicConfig(
    filename='HoltEModelHobbyScraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HoltEModelHobbyScraper:
    def __init__(self):
        self.driver=None
        
    def chrome(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        self.driver.set_window_size(1920, 1080)
        
        self.driver.get("https://holte-modelhobby.dk/")
        time.sleep(3)
        # self.save_cookies("holte-modelhobby_cookies.json") #use when needed to refresh cookies or when cookies file missing
        self.load_cookies("holte-modelhobby_cookies.json")
        self.driver.refresh()

    def save_cookies(self, path):
        with open(path, 'w') as file:
            json.dump(self.driver.get_cookies(), file)

    def load_cookies(self, path):
        with open(path, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        
    def extract_collection_links(self, output_file, url):
        all_links = []
        self.driver.get(url)
        time.sleep(2)  

        wait = WebDriverWait(self.driver, 10)
        sitemap = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.m-sitemap-cat.m-links.list-unstyled")))

        collection_links = sitemap.find_elements(By.TAG_NAME, "a")

        for link in collection_links:
            href = link.get_attribute("href")
            if href:
                all_links.append(href)

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for link in all_links:
                writer.writerow([link])
    
    def get_product_links(self, output_file):
        self.chrome()
        product_links = []
        sitemap_url = "https://holte-modelhobby.dk/sitemap/produkter/"
        self.driver.get(sitemap_url)
        time.sleep(3)  
        page_count = 1

        while True:
            try:
                logging.info(f"Processing page {page_count}...")

                
                product_list = self.driver.find_element(By.CSS_SELECTOR, '.m-sitemap-prod.m-links.list-unstyled')
                product_items = product_list.find_elements(By.CSS_SELECTOR, 'li.m-sitemap-prod-item.m-links-prod a')
                
                page_links = [item.get_attribute('href') for item in product_items]
                product_links.extend(page_links)

                logging.info(f"Extracted {len(page_links)} product links from page {page_count}.")
               
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, '.w-pagination-list a[rel="next"]')
                    if next_button:
                        next_button.click()
                        time.sleep(4)  
                        page_count += 1
                    else:
                        break 
                except Exception as a:
                    logging.error(f"Error occurred on page {page_count}: cant find next button")
                    break

            except Exception as e:
                logging.error(f"Error occurred on page {page_count}: {str(e)}")
                break

      
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for link in product_links:
                writer.writerow([link])

        logging.info(f"Total of {len(product_links)} product links extracted.")
    
    def extract_product_details(self, product_urls_file, output_file, variant_urls_file='holte-modelhobby_variant_urls.csv', failed_urls_file='holte-modelhobby_failed_urls.csv', batch_size=50):
        for file in [output_file, variant_urls_file, failed_urls_file]:
            if os.path.exists(file):
                os.remove(file)

        with open(product_urls_file, 'r') as file:
            product_urls = [line.strip() for line in file]

        with open(output_file, 'a', newline='', encoding='utf-8') as output_csv, \
            open(variant_urls_file, 'a', newline='', encoding='utf-8') as variant_csv, \
            open(failed_urls_file, 'a', newline='', encoding='utf-8') as failed_csv:
            
            writer = csv.writer(output_csv)
            variant_writer = csv.writer(variant_csv)
            failed_writer = csv.writer(failed_csv)

            if os.stat(output_file).st_size == 0:
                writer.writerow(['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'URL'])
            if os.stat(variant_urls_file).st_size == 0:
                variant_writer.writerow(['URL'])
            if os.stat(failed_urls_file).st_size == 0:
                failed_writer.writerow(['URL'])

            for i in range(0, len(product_urls), batch_size):
                batch_urls = product_urls[i:i + batch_size]
                self.process_batch(batch_urls, writer, variant_writer, failed_writer)
                output_csv.flush()
                variant_csv.flush()
                failed_csv.flush()
                gc.collect()
                time.sleep(10)

        self.process_variant_urls(variant_urls_file, output_file, failed_urls_file)

    def process_single_url(self, url, writer, variant_writer, failed_writer):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check for variants
            variants = soup.select('div.m-product-buttons-list-button.data')
            if variants:
                variant_writer.writerow([url])
                logging.info(f"Variants found for {url}. URL added to variant_urls.csv")
                return  # Skip processing and move to next URL

            # Extract product details
            title = soup.select_one('h1.m-product-title.product-title')
            brand = soup.select_one('p.m-product-brand a.m-product-brand-link')
            base_price = soup.select_one('meta[itemprop="price"]')
            sku = soup.select_one('span.m-product-itemNumber-value')
            stock_status_elem = soup.select_one('p.m-productlist-stock-text')

            title_text = title.get_text(strip=True) if title else "N/A"
            brand_text = brand['title'].split(': ')[-1] if brand and brand.has_attr('title') else "N/A"
            price_text = base_price['content'] if base_price and base_price.has_attr('content') else "N/A"
            sku_text = sku.get_text(strip=True) if sku else "N/A"
            stock_status = self.get_stock_status_bs4(stock_status_elem)

            writer.writerow([title_text, brand_text, sku_text, price_text, stock_status, url])
            logging.info(f"Extracted details for {url}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for {url}: {e}")
            failed_writer.writerow([url])  # Append failed URL to file
        except Exception as e:
            logging.error(f"Error extracting details for {url}: {e}")
            failed_writer.writerow([url])  # Append failed URL to file

    def process_batch(self, batch_urls, writer, variant_writer, failed_writer):
        with ThreadPoolExecutor(max_workers=2) as executor:  # Adjust the number of workers as needed
            futures = [executor.submit(self.process_single_url, url, writer, variant_writer, failed_writer) for url in batch_urls]

            for future in as_completed(futures):
                try:
                    future.result()  # Get the result to raise any exceptions
                except Exception as e:
                    logging.error(f"Error in threaded execution: {e}")

    def process_variant_urls(self, variant_urls_file, output_file, failed_urls_file='failed_urls.csv'):
        self.chrome()
        try:
            with open(variant_urls_file, 'r') as file:
                variant_urls = [line.strip() for line in file if line.strip() != 'URL']  # Skip header

            with open(output_file, 'a', newline='', encoding='utf-8') as output_csv, \
                open(failed_urls_file, 'a', newline='', encoding='utf-8') as failed_csv:
                
                writer = csv.writer(output_csv)
                failed_writer = csv.writer(failed_csv)

                # Write headers if the files are empty
                if os.stat(output_file).st_size == 0:
                    writer.writerow(['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'URL'])
                if os.stat(failed_urls_file).st_size == 0:
                    failed_writer.writerow(['URL'])

                for url in variant_urls:
                    try:
                        self.driver.get(url)
                        time.sleep(2)
                        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'zoomHook')))

                        title = self.get_element_text(By.CSS_SELECTOR, 'h1.m-product-title.product-title', default="N/A")
                        brand = self.get_element_attribute(By.CSS_SELECTOR, 'p.m-product-brand a.m-product-brand-link', 'title', default="N/A").split(': ')[-1]
                        base_price = self.get_element_attribute(By.CSS_SELECTOR, 'meta[itemprop="price"]', 'content', default="N/A")
                        sku = self.get_element_text(By.CSS_SELECTOR, 'span.m-product-itemNumber-value', default="N/A")
                        stock_status = self.get_stock_status(By.CSS_SELECTOR, 'p.m-productlist-stock-text')

                        variants = self.driver.find_elements(By.CSS_SELECTOR, 'div.m-product-buttons-list-button.data')
                        if variants:
                            for variant in variants:
                                try:
                                    label = variant.find_element(By.TAG_NAME, 'label')
                                    self.driver.execute_script("arguments[0].click();", label)
                                    time.sleep(2.5)
                                except:
                                    try:
                                        label = variant.find_element(By.TAG_NAME, 'label')
                                        label.click()
                                        time.sleep(2)
                                    except Exception as e:
                                        logging.error(f"Error clicking variant for {url}: {e}")
                                        continue

                                variant_price = self.get_element_text(By.CSS_SELECTOR, 'span.selected-priceLine .price', default="N/A")
                                variant_sku = self.get_element_text(By.CSS_SELECTOR, 'span.product-itemNumber-value.selected-itemNumber-value', default="N/A")
                                variant_stock_status = self.get_stock_status(By.CSS_SELECTOR, 'span.product-stock-text.selected-stock-text')
                                writer.writerow([title, brand, variant_sku, variant_price, variant_stock_status, url])
                                logging.info(f"Extracted variant details for {url}")
                        else:
                            writer.writerow([title, brand, sku, base_price, stock_status, url])
                            logging.info(f"Extracted details for {url} without variants")

                    except Exception as e:
                        logging.error(f"Error processing variant URL {url}: {e}")
                        failed_writer.writerow([url])  # Append failed URL to file

        except FileNotFoundError:
            logging.error(f"{variant_urls_file} not found.")
        except Exception as e:
            logging.error(f"Error processing variant URLs: {e}")

    def get_stock_status_bs4(self, stock_element):
        try:
            # try:
            #     print(stock_text.text)
            # except:
            #     print('cant print stock')
            stock_text = stock_element.get_text(strip=True) if stock_element else ""
            if "Ikke på lager" in stock_text:
                return "Out of Stock"
            elif "På lager" in stock_text:
                return "In Stock"
            elif "Ventes" in stock_text:
                return "Out of Stock(Expected)"
            elif "På fjernlager" in stock_text:
                return "In Stock(in remote storage)"
            else:
                return "N/A"
        except Exception:
            return "N/A"

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
    scraper = HoltEModelHobbyScraper()
    
    url = "https://holte-modelhobby.dk/sitemap/kategorier/"
    collection_file = 'holte-modelhobby_Product_url.csv'
    product_details_file = "holte-modelhobby_details.csv"
    print("Choose an option:")
    print("1. Extract product links and product details")
    print("2. Extract product links")
    print("3. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")

    if option == "1":
        scraper.get_product_links(collection_file)
        time.sleep(50)
        scraper.extract_product_details(collection_file, product_details_file)
    elif option == "2":
        scraper.get_product_links(collection_file)
    elif option =="3":
        scraper.extract_product_details(collection_file, product_details_file)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()