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

url = 'https://www.varomoney.com/blog/'
driver.get(url)

time.sleep(3)

blog_titles = []
blog_authors = []
blog_dates = []
blog_contents = []


container = driver.find_element(By.CLASS_NAME, "swiper-wrapper")

blog_items = container.find_elements(By.CLASS_NAME, "swiper-slide")
blog_links = [] 

for blog in blog_items:
    blogs_link = blog.find_element(By.TAG_NAME, "a")
    blog_links.append(blogs_link.get_attribute("href"))

    
for blog_page in blog_links:
    driver.get(blog_page)
    try:
        time.sleep(3)
        blog_title = driver.find_element(By.CLASS_NAME, "BlogArticle_headline__UUClM").text
        blog_date_author = driver.find_element(By.CLASS_NAME, "BlogArticle_dateAuthor__A0tGF").text
        blog_date = blog_date_author.split("•")[0]
        blog_author = blog_date_author.split("•")[1]
        blog_content = driver.find_element(By.CLASS_NAME, "BlogArticle_bodyContent__NYDoz").text

        blog_titles.append(blog_title)
        blog_authors.append(blog_author)
        blog_dates.append(blog_date)
        blog_contents.append(blog_content)

    except Exception as e:
        logger.error(f"Error scraping article at {blog_page}: {e}")


data = {
    'website':'varo',
    'title': blog_titles,
    'author': blog_authors,
    'date': blog_dates,
    'content': blog_contents
}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"varo_blogs_{timestamp}.csv"

S3Utils.Upload(S3.S3_BLOGS_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_BLOGS_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")

driver.quit()

