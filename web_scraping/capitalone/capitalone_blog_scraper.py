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

urls = [
    "https://www.capitalone.com/about/our-commitments/",
    'https://www.capitalone.com/about/newsroom/',
    "https://www.capitalone.com/about/insights-center/",
    "https://www.capitalone.com/tech/"
]


blog_titles = []
blog_dates = []
blog_contents = []
blog_urls = []


for url in urls:
    blog_links = [] 
    driver.get(url)
    time.sleep(3)

    while True:
        try:
            load_more_button = driver.find_element(By.XPATH, "//button[@data-initial-value='Load more']")
            load_more_button.click()
            time.sleep(2)  
        except Exception as e:
            break

    blog_items = driver.find_elements(By.TAG_NAME, "shared-article-tile")
    for blog in blog_items:
        blogs_link = blog.find_element(By.TAG_NAME, "a")
        blog_links.append(blogs_link.get_attribute("href"))
        
    for blog_page in blog_links:
        driver.get(blog_page)
        try:
            time.sleep(3)
            blog_title = driver.find_element(By.CLASS_NAME, "headline").text
            blog_date =  driver.find_element(By.XPATH, "//span[@class='ng-star-inserted']").text
            blog_content_element = driver.find_element(By.XPATH, "//div[contains(@class,'article-body-content')]")
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
    'website':'capital one',
    'title': blog_titles,
    'date': blog_dates,
    'content': blog_contents,
    'blog_url':blog_urls
}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"capitalone_blogs_{timestamp}.csv"

S3Utils.Upload(S3.S3_BLOGS_DIRECTORY, file_name, data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name, data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_BLOGS_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully")

driver.quit()
