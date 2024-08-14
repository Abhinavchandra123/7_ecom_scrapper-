from ecom2 import MorfarsScraper
from ecom3 import SpeedHobby_Scraper
from ecom4 import RcklubbenScraper
from ecom5 import HobbyKarlScraper
from ecom6 import ModelSportScraper
from ecom7 import HoltEModelHobbyScraper

def run_morfars_scraper():
    scraper = MorfarsScraper()

    url = 'https://morfars.dk/collections/all'
    product_urls = "morfars_product_urls.csv"
    product_details = "morfars_product_details.csv"

    print("Starting MorfarsScraper...")
    print("Extracting product links...")
    scraper.extract_product_links(url, product_urls)
    print("Product links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(product_urls, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("MorfarsScraper execution completed.")

def run_speedhobby_scraper():
    scraper = SpeedHobby_Scraper()

    url = "https://speedhobby.se"
    output_file = 'speedhobby_collections.csv'
    product_urls = "speedhobby_urls.csv"
    product_details = "speedhobby_details.csv"

    print("Starting SpeedHobby_Scraper...")
    print("Extracting collection links...")
    scraper.extract_collection_links(output_file, url)
    print("Collection links extracted successfully.")

    print("Extracting product links...")
    scraper.get_product_links(output_file, product_urls)
    print("Product links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(product_urls, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("SpeedHobby_Scraper execution completed.")

def run_rcklubben_scraper():
    scraper = RcklubbenScraper()

    url = "https://rcklubben.se/"
    output_file = 'rcklubben_collections.csv'
    product_urls = "rcklubben_urls.csv"
    product_details = "rcklubben_details.csv"

    print("Starting RcklubbenScraper...")
    print("Extracting collection links...")
    scraper.extract_collection_links(output_file, url)
    print("Collection links extracted successfully.")

    print("Extracting product links...")
    scraper.get_product_links(output_file, product_urls)
    print("Product links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(product_urls, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("RcklubbenScraper execution completed.")

def run_hobbykarl_scraper():
    scraper = HobbyKarlScraper()

    url = "https://hobbykarl.dk/sitemap/kategorier/"
    output_file = 'hobbykarl_collections.csv'
    product_urls = "hobbykarl_urls.csv"
    product_details = "hobbykarl_details.csv"

    print("Starting HobbyKarlScraper...")
    print("Extracting collection links...")
    scraper.extract_collection_links(output_file, url)
    print("Collection links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(output_file, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("HobbyKarlScraper execution completed.")

def run_modelsport_scraper():
    scraper = ModelSportScraper()
    
    url = "https://modelsport.dk/"
    output_file = 'modelsport_collections.csv'
    product_urls = "modelsport_urls.csv"
    product_details = "modelsport_details.csv"
    
    print("Starting ModelSportScraper...")
    print("Extracting collection links...")
    scraper.extract_collection_links(output_file, url)
    print("Collection links extracted successfully.")

    print("Extracting product links...")
    scraper.get_product_links(output_file, product_urls)
    print("Product links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(product_urls, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("ModelSportScraper execution completed.")

def run_holtemodelhobby_scraper():
    scraper = HoltEModelHobbyScraper()

    url = "https://holtmodelhobby.dk/"
    output_file = 'holtemodelhobby_collections.csv'
    product_urls = "holtemodelhobby_urls.csv"
    product_details = "holtemodelhobby_details.csv"

    print("Starting HoltEModelHobbyScraper...")
    print("Extracting collection links...")
    scraper.extract_collection_links(output_file, url)
    print("Collection links extracted successfully.")

    print("Extracting product links...")
    scraper.get_product_links(output_file, product_urls)
    print("Product links extracted successfully.")

    print("Extracting product details...")
    scraper.extract_product_details(product_urls, product_details)
    print("Product details extracted successfully.")

    scraper.close_driver()
    print("HoltEModelHobbyScraper execution completed.")

if __name__ == "__main__":
    run_morfars_scraper()
    run_speedhobby_scraper()
    run_rcklubben_scraper()
    run_hobbykarl_scraper()
    run_modelsport_scraper()
    run_holtemodelhobby_scraper()
