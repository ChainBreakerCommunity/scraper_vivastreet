###################################
###        VIVA STREET          ###
###################################
import time
import bot.constants_uk
import bot.constants_ireland
import bot.scrape
import sys
import logging
import warnings
from chainbreaker_api import ChainBreakerScraper

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.env import get_config
config = get_config()

#from dotenv import dotenv_values
#debug_config = dotenv_values(".env.development")

warnings.filterwarnings("ignore")

def enterVivaStreet(constants, driver: webdriver):
    driver.get(constants.SITE)
    print("Current URL: ", driver.current_url)
    #WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.ID, "accept-disclaimer")))
    time.sleep(5)
    
    button = driver.find_element(By.ID, "accept-disclaimer")
    button.click()

    # Select asian filter.
    driver.find_element(By.XPATH, "//select[@id='vs_searchform_common_second_type']/option[text()='Asian']").click()
    search_button = driver.find_element(By.ID, "search-button")
    search_button.click()

def main(constants):
    endpoint = config["ENDPOINT"]
    user = config["USERNAME"]
    password = config["PASSWORD"]

    #logging.warning("Parameters passed to scraper: " + endpoint + ", " + user + ", " + password)
    #print("Parameters passed to scraper: " + endpoint + ", " + user + ", " + password)
    #sys.stdout.flush()

    client = ChainBreakerScraper(endpoint)
    print("Trying to login now")
    res = client.login(user, password)
    if type(res) != str:
        logging.critical("Login was not successful.")
        print("Login was not successful.")
        sys.stdout.flush()
        sys.exit()
    else: 
        logging.warning("Login was successful.")
        print("Login was successful.")
        sys.stdout.flush()

    # Crear driver.
    print("Open Chrome")

    if bool(config["DEBUG"]) == True:
        driver = webdriver.Chrome(executable_path="./chromedriver.exe")
    else:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = config["GOOGLE_CHROME_BIN"]
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(executable_path= config["CHROMEDRIVER_PATH"], chrome_options=chrome_options)

    wait = WebDriverWait(driver, 10)
    #driver = webdriver.Remote(selenium_endpoint, desired_capabilities=DesiredCapabilities.FIREFOX)
    enterVivaStreet(constants, driver)
    count_announcement = 1

    # Page lists.
    for page in range(2, constants.MAX_PAGES + 1):
        logging.warning("# Page: " + str(page))
        print("# Page: " + str(page))
        sys.stdout.flush()
    
        # Get list of ads.
        ads = driver.find_elements(By.CLASS_NAME, "clad")
        # Iterate over ads.
        for ad in ads:
            url = ad.find_element(By.CLASS_NAME, "clad__ad_link").get_attribute("href") 
            
            if client.get_status() != 200:
                logging.error("Endpoint is offline. Service stopped.", exc_info = True)
                driver.quit()
                sys.exit()
            info_ad = constants.SITE_NAME + ", #ad " + str(count_announcement) + ", page_link " + url
            id_ad = ad.get_attribute("data-clad-id") 

            if client.does_ad_exist(id_ad, constants.SITE_NAME, constants.COUNTRY):
                logging.warning("Ad already in database. Link: " + url)
                print("Ad already in database. Link: " + url)
                sys.stdout.flush()
                continue
            else:
                logging.warning("New Ad. " + info_ad)
                print("New Ad. " + info_ad)
                sys.stdout.flush()

            region, city, place = bot.scrape.getLocation(ad)
            isFeature = bot.scrape.isFeature(ad)
            isVerified = bot.scrape.isVerified(ad)

            # Enter to the ad.
            original_window = driver.current_window_handle
            assert len(driver.window_handles) == 1

            # Click the link which opens in a new window
            driver.execute_script("window.open('');")

            # Wait for the new window or tab
            wait.until(EC.number_of_windows_to_be(2))

            # Loop through until we find a new window handle
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            
            # Load ad in the new window.
            driver.get(url)

            logging.warning("Ad correctly loaded.")
            print("Ad correctly loaded.")
            sys.stdout.flush()

            # Save values in dictionary.
            dicc = {}
            dicc["region"] = region
            dicc["city"] = city
            dicc["place"] = place
            dicc["id_ad"] = id_ad
            dicc["url"] = url
            dicc["isFeature"] = isFeature
            dicc["isVerified"] = isVerified

            # Scrap ad.
            ad_record = bot.scrape.scrap_ad_link(constants, client, driver, dicc)
            count_announcement += 1

            # Return to pagination.
            #driver.get(current_url)
            driver.close()
            driver.switch_to.window(original_window)

        # Return the menu.
        #driver.get(constants.PAGINATION + str(page))
        # Change pagination with button.
        try:
            elements = driver.find_elements(By.CLASS_NAME, "kiwii-btn")
            for ele in elements: 
                if ele.text == "»":
                    ele.click()
        except:
            continue
    driver.quit()

def execute_scraper():
    main(constants = bot.constants_uk)
    main(constants = bot.constants_ireland)

if __name__ == "__main__":
    execute_scraper()