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


blog_titles = []
blog_authors = []
blog_dates = []
blog_contents = []
blog_urls = []

urls = [
    "https://www.chime.com/blog/category/banking-basics/",
    "https://www.chime.com/blog/category/payday/",
    "https://www.chime.com/blog/category/loans/",
    "https://www.chime.com/blog/category/money-habits/",
    "https://www.chime.com/blog/category/credit/",
    "https://www.chime.com/blog/category/safety-and-security/",
    "https://www.chime.com/blog/category/managing-debt/",
    "https://www.chime.com/blog/category/taxes/",
    "https://www.chime.com/blog/category/chime-guides/",
    "https://www.chime.com/blog/category/calculators/"
]
for url in urls:
    try:
        driver.get(url)
        time.sleep(3) 

        post_urls = []

        while True:
            try:
                posts = driver.find_elements(By.CSS_SELECTOR, ".content-hub-category-explore__posts .content-hub-post")
                for post in posts:
                    post_link = post.find_element(By.CSS_SELECTOR, ".content-hub-post__link").get_attribute('href')
                    post_urls.append(post_link)

                time.sleep(2)

                next_button = driver.find_element(By.CSS_SELECTOR, ".content-hub-pagination__arrow--next")

                if 'content-hub-pagination__arrow--disabled' in next_button.get_attribute('class'):
                    break

                next_button.click()

                time.sleep(2)
            except Exception as e:
                logger.error(f"An error occurred while scraping category pages: {e}")
                break

        for post_url in post_urls:
            driver.get(post_url)
            try:
                blog_title = driver.find_element(By.CLASS_NAME, "blog-template__title").text
                blog_author = driver.find_element(By.CLASS_NAME, "blog-template__details-author").text
                blog_date = driver.find_element(By.CLASS_NAME, "blog-template__details-date").text
                blog_content = driver.find_element(By.CLASS_NAME, "blog-template__article").text

                blog_titles.append(blog_title)
                blog_authors.append(blog_author)
                blog_dates.append(blog_date)
                blog_contents.append(blog_content)
                blog_urls.append(post_url)


            except Exception as e:
                logger.error(f"Error scraping article at {post_url}: {e}")

    except Exception as e:
        logger.error(f"Error processing category {url}: {e}")
        continue

data = {
    'website':'chime',
    'title': blog_titles,
    'author': blog_authors,
    'date': blog_dates,
    'content': blog_contents,
    'blog_url':blog_urls

}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"chime_blogs_{timestamp}.csv"

S3Utils.Upload(S3.S3_BLOGS_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_BLOGS_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")

driver.quit()

