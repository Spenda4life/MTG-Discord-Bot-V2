from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time


def get_moxfield_decklist(link, download = False):

    prefs = {
        "download.default_directory": r'C:\Users\Mike\Documents\Code\Python\WebScraping\downloads',
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
        }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(30)

    driver.get(link)

    download_button  = driver.find_element(By.LINK_TEXT, "Download")
    download_button.click()

    decklist_element = driver.find_element(By.CSS_SELECTOR, 'textarea[name="full"]')
    decklist_text = decklist_element.get_attribute("value")

    if download == True:
        mtgo_button = driver.find_element(By.LINK_TEXT, 'Download for MTGO')
        mtgo_button.click()
        time.sleep(5)

    driver.quit()

    return decklist_text


def parse_decklist(moxfield_decklist_text):
    decklist = []
    for line in moxfield_decklist_text.split('\n'):
        decklist.append(line[:line.find('(')].strip())
    return decklist


decklist = get_moxfield_decklist('https://www.moxfield.com/decks/zD3I9kSPaUmDmPIrIk_Mtg')
print(decklist)