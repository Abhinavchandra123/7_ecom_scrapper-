import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging for HobbyKarlScraper
logging.basicConfig(
    filename='HobbyKarlScraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HobbyKarlScraper:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        options.add_argument("--headless") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.set_window_size(1920, 1080)
    
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
        
        logging.info(f"Extracted {len(all_links)} collection links.")

    def extract_product_details(self, collection_file, output_file):
        def extract_details_from_page(url):
            self.driver.get(url)
            time.sleep(5)
            
            product_details = []
            while True:
                products = self.driver.find_elements(By.CSS_SELECTOR, '.productItem')
                for product in products:
                    try:
                        try:
                            name_element = product.find_element(By.CSS_SELECTOR, '.m-productlist-title')
                            product_name = name_element.text
                        except:
                            product_name = "N/A"
                        
                        try:
                            brand_element = product.find_element(By.CSS_SELECTOR, '.m-productlist-brand')
                            product_brand = brand_element.text
                        except:
                            product_brand = "N/A"
                        
                        try:
                            sku_element = product.find_element(By.CSS_SELECTOR, '.m-productlist-itemNumber')
                            product_sku = sku_element.text
                        except:
                            product_sku = "N/A"
                        
                        try:
                            price_element = product.find_element(By.CSS_SELECTOR, '.m-productlist-price')
                            product_price = price_element.text
                        except:
                            product_price = "N/A"
                        
                        try:
                            stock_status_element = product.find_element(By.CSS_SELECTOR, '.product-delivery .stockAmount')
                            stock_status = stock_status_element.text
                        except:
                            try:
                                sold_out_badge = product.find_element(By.CSS_SELECTOR, '.badge-danger.m-productlist-soldout')
                                stock_status = sold_out_badge.text
                            except:
                                try:
                                    stock_status_text = product.find_element(By.CSS_SELECTOR, '.product-delivery p')
                                    stock_status = stock_status_text.text
                                except:
                                    stock_status = "In stock"
                        
                        try:
                            link_element = product.find_element(By.CSS_SELECTOR, '.productItem a')
                            product_link = link_element.get_attribute('href')
                        except:
                            product_link = "N/A"
                        
                        product_details.append({
                            'Product Name': product_name,
                            'Brand': product_brand,
                            'SKU': product_sku,
                            'Price': product_price,
                            'Stock Status': stock_status,
                            'URL': product_link
                        })
                        
                    except Exception as e:
                        logging.error(f"Error extracting product details: {e}")
                
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.pagination li:last-child a'))
                    )
                    
                    next_button_class = next_button.find_element(By.XPATH, '..').get_attribute('class')

                    if 'is-disabled' in next_button_class:
                        break  

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(2) 

                    next_button.click()
                    time.sleep(5)  

                except Exception as e:
                    logging.error(f"Pagination button not found or error: {e}")
                    break  
            
            return product_details

        with open(collection_file, "r") as file:
            reader = csv.DictReader(file)
            collection_urls = [row['Collection Link'] for row in reader]

        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Product Name', 'Brand', 'SKU', 'Price', 'Stock Status', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for url in collection_urls:
                product_details = extract_details_from_page(url)
                for details in product_details:
                    writer.writerow(details)
        
        logging.info(f"Extracted product details for {len(collection_urls)} collection pages.")

    def close_driver(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = HobbyKarlScraper()
    
    url = "https://hobbykarl.dk/sitemap/kategorier/"
    output_file = 'hobbykarl_collections.csv'
    product_urls = "hobbykarl_urls.csv"
    product_details = "hobbykarl_details.csv"
    
    print("Choose an option:")
    print("1. Extract collection links")
    print("2. Extract product details from product links")
    option = input("Enter the option number (1, 2, or 3): ")
    
    print("Starting HobbyKarlScraper...")
    print("Extracting collection links...")
    if option == "1":
        scraper.extract_collection_links(output_file, url)
        print("Collection links extracted successfully.")
    elif option == "2":
        print("Extracting product details...")
        scraper.extract_product_details(output_file, product_details)
        print("Product details extracted successfully.")
    else:
        print("Invalid option. Please run the script again and choose a valid option.")

    scraper.close_driver()
    print("HobbyKarlScraper execution completed.")
