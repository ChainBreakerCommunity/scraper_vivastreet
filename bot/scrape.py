import datetime
from chainbreaker_api import ChainBreakerScraper
from selenium.webdriver.common.by import By
import selenium
import sys 
from logger.logger import get_logger
logger = get_logger(__name__, level = "DEBUG", stream = True)


def clean_string(string, no_space = False):   
    """
    Clean String.
    """
    if no_space:
        string = string.replace("  ","")
    string = string.strip()
    string = string.lower()
    string = string.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    string = string.replace("\n"," ")
    return string

def getId(driver: selenium.webdriver):
    id_box = driver.find_element(By.CLASS_NAME, "kiwii-description-footer")
    number = id_box.text.split()[2]
    return number

def getTitle(driver: selenium.webdriver):
    title = driver.find_element(By.TAG_NAME, "h1")
    return title.text

def getLocation(ad: selenium.webdriver.remote.webelement.WebElement):
    geo = ad.find_element(By.CLASS_NAME, "clad__geo")
    divs = geo.find_elements(By.TAG_NAME, "div")
    region = divs[1].text
    city = divs[1].text
    try:
        place = divs[2].text
    except:
        place = ""
    if place == city:
        place = ""
    return region, city, place

def getText(driver: selenium.webdriver) -> str:
    text = driver.find_element(By.CLASS_NAME, "shortdescription")
    text = text.text.replace("\n", " ")
    return text

def getCategory(category: str) -> str:
    return category

def getAge(driver: selenium.webdriver) -> str:
    value = ""
    trs = driver.find_elements(By.TAG_NAME, "tr")
    keywords = ["Age "]
    for word in keywords:
        for tr in trs: 
            if word in tr.text:
                value = tr.text[len(word):].split()[0]
                break
    return value

def getEthnicity(driver: selenium.webdriver) -> str:
    value = ""
    addSlash = True
    trs = driver.find_elements(By.TAG_NAME, "tr")
    keywords = ["Ethnicity", "Nationality"]
    for word in keywords:
        for tr in trs: 
            if word in tr.text:
                value += tr.text[len(word) + 1:].split()[0]
                if addSlash: 
                    value += "/"
                    addSlash = False

    return value

def getPostDate(driver):
    return datetime.date.today()

def getCellphone(constants, driver: selenium.webdriver) -> str:
    try:
        cellphone = driver.find_element(By.ID, "phone_link_bottom")
        cellphone = cellphone.get_attribute("onclick")
        start = cellphone.find("tel:") + 4
        end = cellphone.find("';")
        cellphone = cellphone[start:end]
        if constants.COUNTRY_PREFIX in cellphone:
            cellphone = cellphone.replace(constants.COUNTRY_PREFIX, "")
        return cellphone
    except:
        return None

def getDateScrap() -> datetime.datetime:
    return datetime.date.today()

def isVerified(ad: selenium.webdriver.remote.webelement.WebElement) -> str: 
    try:
        ad.find_element(By.CLASS_NAME, "verified-badge")
        return "1"
    except: 
        return "0"

def isFeature(ad: selenium.webdriver.remote.webelement.WebElement) -> str:
    try:
        ad.find_element(By.CLASS_NAME, "label-badge-featured")
        return "1"
    except: 
        return "0"
    #if label.text == "FEATURED":
    #    promoted_ad = "1"
    #return promoted_ad

def scrap_ad_link(constants, client: ChainBreakerScraper, driver, dicc: dict):
    
    # Get phone or whatsapp
    phone = getCellphone(constants, driver)
    email = ""
    if phone == None:
        logger.warning("Phone not found! Skipping this ad.")
        return None
    
    author = constants.AUTHOR
    language = constants.LANGUAGE
    link = dicc["url"]
    id_page = getId(driver)
    title = getTitle(driver)
    text = getText(driver)
    category = constants.CATEGORY
    first_post_date = getPostDate(driver)

    date_scrap = getDateScrap()
    website = constants.SITE_NAME

    verified_ad = dicc["isVerified"]
    prepayment = ""
    promoted_ad = dicc["isFeature"]
    external_website = ""
    reviews_website = ""
    country = constants.COUNTRY 
    region = clean_string(dicc["region"])
    city = clean_string(dicc["city"])
    place = clean_string(dicc["place"])

    comments = []
    latitude = ""
    longitude = ""

    temp_value = getEthnicity(driver).split("/")
    ethnicity = temp_value[0]
    nationality = temp_value[1]

    age = getAge(driver)

    # Upload ad in database.
    data, res = client.insert_ad(author, language, link, id_page, title, text, category, first_post_date, date_scrap, website, phone, country, region, city, place, email, verified_ad, prepayment, promoted_ad, 
            external_website, reviews_website, comments, latitude, longitude, ethnicity, nationality, age) # Eliminar luego
    #status_code = res.status_code

    # Log results.
    logger.info("Data sent to server: ")
    logger.info(data)
    logger.info(res.status_code)
    #print(res.text)
    if res.status_code != 200: 
        logger.error("Algo salió mal...")
    else: 
        logger.info("Éxito!")