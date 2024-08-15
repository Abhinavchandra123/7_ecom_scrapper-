import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class HoltEModelHobbyScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
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
    
    def get_product_links(self, collection_file, output_file):
        pass
    
    def extract_product_details(self, product_urls_file, output_file):
        product_details = []

        with open(product_urls_file, 'r') as file:
            urls = [line.strip() for line in file]

        for url in urls:
            self.driver.get(url)
            time.sleep(4) 

            while True:  
                try:
                    try:
                        wait = WebDriverWait(self.driver, 10)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.productItem")))
                    except:
                        pass
                    products = self.driver.find_elements(By.CSS_SELECTOR, "div.productItem")

                    for product in products:
                        try:
                            # Extract product link
                            try:
                                product_link = product.find_element(By.CSS_SELECTOR, "a.m-productlist-link").get_attribute("href")
                            except Exception as e:
                                print(f"Error extracting product link")
                                product_link = 'N/A'

                            # Extract product title
                            try:
                                title_element = product.find_element(By.CSS_SELECTOR, "p.m-productlist-title")
                                product_title = title_element.text if title_element else 'N/A'
                            except Exception as e:
                                print(f"Error extracting product title")
                                product_title = 'N/A'

                            # Extract product SKU
                            try:
                                sku_element = product.find_element(By.CSS_SELECTOR, "p.m-productlist-itemNumber")
                                product_sku = sku_element.text if sku_element else 'N/A'
                            except Exception as e:
                                print(f"Error extracting product SKU")
                                product_sku = 'N/A'

                            # Extract product brand
                            try:
                                brand_element = product.find_element(By.CSS_SELECTOR, "span.m-productlist-brand")
                                product_brand = brand_element.text if brand_element else 'N/A'
                            except Exception as e:
                                print(f"Error extracting product brand")
                                product_brand = 'N/A'

                            # Extract product price
                            try:
                                price_element = product.find_element(By.CSS_SELECTOR, "span.m-productlist-price")
                                product_price = price_element.text if price_element else 'N/A'
                            except Exception as e:
                                print(f"Error extracting product price")
                                product_price = 'N/A'

                            # Extract stock status
                            try:
                                out_of_stock_icon = product.find_element(By.CSS_SELECTOR, "i.no-stock-icon")
                                stock_status = "Out of Stock"
                            except Exception as e:
                                try:
                                    in_stock_icon = product.find_element(By.CSS_SELECTOR, "i.in-stock-icon")
                                    stock_status = "In Stock"
                                except Exception as e:
                                    print(f"Error extracting stock status")
                                    stock_status = "N/A"  # Default to "In Stock" if neither icon is found

                            product_details.append([product_title, product_brand, product_sku, product_price, stock_status, product_link])

                        except Exception as e:
                            print(f"Error processing product: {e}")
                            return  # Exit the function if any critical element can't be located

                    # Check for and click the "Next" button
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, '.productpagination .pagination li:not(.is-disabled) a[data-ng-click*="next"]')
                        if next_button:
                            next_button.click()
                            time.sleep(4)  # Allow time for the next page to load
                        else:
                            break  # No more pages to process
                    except Exception as e:
                        print(f"Pagination ended")
                        break  # Exit the loop if there's an error or no next button

                except Exception as e:
                    print(f"Error extracting details from {url}: {e}")
                    break  # Exit the loop if there's an error loading the page or finding products

        # Save the extracted details to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Brand', 'SKU', 'Price', 'Stock Status', 'Product Link'])
            writer.writerows(product_details)

        print(f"Product details extracted and saved to {output_file}")

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = HoltEModelHobbyScraper()
    
    url = "https://holte-modelhobby.dk/sitemap/kategorier/"
    collection_file = 'holte-modelhobby_collections.csv'
    product_details_file = "holte-modelhobby_details.csv"
    print("Choose an option:")
    print("1. Extract collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")

    if option == "1":
        scraper.extract_collection_links(collection_file, url)
    elif option == "2":
        scraper.extract_product_details(collection_file, product_details_file)
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()