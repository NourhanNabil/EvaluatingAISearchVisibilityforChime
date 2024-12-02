import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import pandas as pd
from datetime import datetime
import logging

from Utils.S3Utils import S3Utils
from Config.S3 import S3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))


product_titles = []
product_contents = []
product_urls = []

urls = [
    "https://help.chime.com/hc/en-us/articles/5438300132631-What-is-SpotMe",
    "https://help.chime.com/hc/en-us/articles/17193149287063-What-is-Safer-Credit-Building",
    "https://help.chime.com/hc/en-us/articles/17192694520983-What-is-Credit-Builder-and-how-can-I-enroll",
    "https://help.chime.com/hc/en-us/articles/20824325253655-What-is-Chime-s-Virtual-Card",
    "https://help.chime.com/hc/en-us/articles/23317674703511-What-s-MyPay",
    "https://help.chime.com/hc/en-us/articles/1500011981082-What-s-a-temporary-credit",
    "https://help.chime.com/hc/en-us/articles/221487887-What-is-the-Chime-Savings-Account"
]
for url in urls:
    try:
        driver.get(url)
        time.sleep(3) 

        post_urls = []

        try:
            product_title = driver.find_element(By.XPATH, "//header//h1").text
            product_content = driver.find_element(By.XPATH, "//div[@class='article-body markdown']").text

            product_titles.append(product_title)
            product_contents.append(product_content)
            product_urls.append(url)


        except Exception as e:
            logger.error(f"Error scraping article  {e}")

    except Exception as e:
        logger.error(f"Error processing category {url}: {e}")
        continue

data = {
    'website':'chime',
    'product_title': product_titles,
    'product_contents': product_contents,
    'product_url':product_urls

}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"chime_products_{timestamp}.csv"

S3Utils.Upload(S3.S3_PRODUCTS_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_PRODUCTS_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")

driver.quit()

