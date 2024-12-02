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
from bs4 import BeautifulSoup
import logging

from Utils.S3Utils import S3Utils
from Config.S3 import S3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

url ="https://www.sofi.com/blog/"
driver.get(url)
time.sleep(3)


blog_links = [] 
blog_titles = []
blog_dates = []
blog_contents = []
blog_urls = []

while True:
    try:
        blog_items = driver.find_elements(By.TAG_NAME, "article")
        for blog in blog_items:
            blogs_link = blog.find_element(By.TAG_NAME, "a")
            blog_links.append(blogs_link.get_attribute("href"))
        
        next_button = driver.find_element(By.XPATH, "//a[@class='nextpostslink']")
        next_page_url = next_button.get_attribute("href")

        driver.get(next_page_url)
        time.sleep(5)  
    except Exception as e:
        break

for blog_page in blog_links:
    driver.get(blog_page)
    try:
        time.sleep(3)
        blog_title = driver.find_element(By.TAG_NAME, "h1").text
        blog_date_text =  driver.find_element(By.XPATH, "//div[@class='post__content--byline']//span").text
        blog_date = blog_date_text.split("|")[0]
        blog_content_element = driver.find_element(By.XPATH, "//div[@class='post__content--post']")
        blog_content_html = blog_content_element.get_attribute("innerHTML")
        soup = BeautifulSoup(blog_content_html, 'html.parser')
        blog_content = soup.get_text(separator=' ', strip=True)
        
        blog_titles.append(blog_title)
        blog_dates.append(blog_date)
        blog_contents.append(blog_content)
        blog_urls.append(blog_page)

    except Exception as e:
        logger.error(f"Error scraping article at {blog_page}: {e}")
   
data = {
    'website':'sofi',
    'title': blog_titles,
    'date': blog_dates,
    'content': blog_contents,
    'blog_url':blog_urls
}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"sofi_blogs_{timestamp}.csv"

S3Utils.Upload(S3.S3_BLOGS_DIRECTORY, file_name, data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name, data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_BLOGS_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully")

driver.quit()
