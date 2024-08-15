import csv
import json
import logging
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
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.set_window_size(1920, 1080)
        
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

    def get_product_links(self, collection_file, output_file):
        product_links = []

        with open(collection_file, 'r') as file:
            reader = csv.reader(file)
            collection_urls = [row[0] for row in reader]

        for url in collection_urls:
            self.driver.get(url.strip())
            time.sleep(3)

            while True:
                products = self.driver.find_elements(By.CSS_SELECTOR, '.productItem .productContent .product-description .m-productlist-heading a.is-block.m-productlist-link')
                for product in products:
                    product_link = product.get_attribute('href')
                    product_links.append(product_link)

                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, '.productpagination .pagination li:not(.is-disabled) a[data-ng-click*="next"]')
                    next_button.click()
                    time.sleep(3)
                    WebDriverWait(self.driver, 10).until(EC.staleness_of(products[0]))
                except Exception as e:
                    logging.info("Pagination ended or error: " + str(e))
                    break

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for link in product_links:
                writer.writerow([link])
        
        logging.info(f"Extracted {len(product_links)} product links.")

    def extract_product_details(self, product_urls, output_file):
        with open(product_urls, 'r') as file:
            product_urls = [line.strip() for line in file]

        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            if file.tell() == 0:
                writer.writerow(['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'URL'])

            for url in product_urls:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'zoomHook')))
                time.sleep(2)
                try:
                    try:
                        title = self.driver.find_element(By.CSS_SELECTOR, 'h1.m-product-title.product-title').text
                    except Exception:
                        title = "N/A"

                    try:
                        brand_element = self.driver.find_element(By.CSS_SELECTOR, 'p.m-product-brand a.m-product-brand-link')
                        brand = brand_element.get_attribute('title').split(': ')[1]
                    except Exception:
                        brand = "N/A"

                    try:
                        base_price = self.driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]').get_attribute('content')
                    except Exception:
                        base_price = "N/A"

                    try:
                        sku_element = self.driver.find_element(By.CSS_SELECTOR, 'span.m-product-itemNumber-value')
                        sku = sku_element.text
                    except Exception:
                        sku = "N/A"

                    try:
                        stock_element = self.driver.find_element(By.CSS_SELECTOR, 'span.m-product-stock-text')
                        stock_status = stock_element.text
                        if "Ikke på lager" in stock_status:
                            stock_status = "Out of Stock"
                        elif "På Lager" in stock_status:
                            stock_status = "In Stock"
                    except Exception:
                        stock_status = "N/A"
                    
                    variants = self.driver.find_elements(By.CSS_SELECTOR, 'div.m-product-buttons-list-button.data')
                    if variants:
                        for variant in variants:
                            try:
                                variant_label = variant.find_element(By.TAG_NAME, 'label')
                                variant_label.click()
                                time.sleep(2)
                                try:
                                    variant_price = self.driver.find_element(By.CSS_SELECTOR, 'span.selected-priceLine .price').text
                                except Exception:
                                    variant_price = "N/A"

                                try:
                                    variant_sku = self.driver.find_element(By.CSS_SELECTOR, 'span.product-itemNumber-value.selected-itemNumber-value').text
                                except Exception:
                                    variant_sku = "N/A"

                                try:
                                    stock_status = self.driver.find_element(By.CSS_SELECTOR, 'span.product-stock-text.selected-stock-text').text
                                    if "Ikke på lager" in stock_status:
                                        stock_status = "Out of Stock"
                                    elif "På Lager" in stock_status:
                                        stock_status = "In Stock"
                                except Exception:
                                    stock_status = "N/A"
                                writer.writerow([title, brand, variant_sku, variant_price, stock_status, url])
                            except Exception as e:
                                logging.error(f"Error extracting variant details for {url}: {e}")
                    else:
                        writer.writerow([title, brand, sku, base_price, stock_status, url])

                except Exception as e:
                    logging.error(f"Error extracting details for {url}: {e}")

        logging.info(f"Extracted product details for {len(product_urls)} products.")

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ModelSportScraper()
    
    url = "https://modelsport.dk/"
    output_file = 'modelsport_collections.csv'
    product_urls = "modelsport_urls.csv"
    product_details = "modelsport_details.csv"
    
    print("Choose an option:")
    print("1. Extract collection links")
    print("2. Extract product links from collection links")
    print("3. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")

    if option == "1":
        scraper.extract_collection_links(output_file, url)
    elif option == "2":
        scraper.get_product_links(output_file, product_urls)
    elif option == "3":
        scraper.extract_product_details(product_urls, product_details)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
    print("ModelSportScraper execution completed.")
