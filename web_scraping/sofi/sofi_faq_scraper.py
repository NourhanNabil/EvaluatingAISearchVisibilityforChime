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

url = 'https://www.sofi.com/faq/'
driver.get(url)

time.sleep(10)

questions = []
answers = []

faq_categories = driver.find_elements(By.CLASS_NAME, "js-copy-expander-v2")

for category in faq_categories:
    try:
        click_category = category.find_element(By.TAG_NAME,'a')
        click_category.click()
        time.sleep(3)

        faq_list = category.find_elements(By.CLASS_NAME, "faq-item")
        
        for faq in faq_list:
            try:
                question_element = faq.find_element(By.TAG_NAME, "h3")
                question_inner_html = question_element.get_attribute("innerHTML")
                question_soup = BeautifulSoup(question_inner_html, "html.parser")
                question = question_soup.get_text(separator=" ").strip()

                answer_element = faq.find_element(By.CLASS_NAME, "faq-answer")
                answer_inner_html = answer_element.get_attribute("innerHTML")
                answer_soup = BeautifulSoup(answer_inner_html, "html.parser")
                answer = answer_soup.get_text(separator=" ").strip()

                if question and answer:
                    questions.append(question)
                    answers.append(answer)
            except Exception as faq_error:
                logger.error(f"Error processing FAQ: {faq_error}")
                continue
    except Exception as category_error:
        logger.error(f"Error processing category: {category_error}")
        continue

data = {'website':"sofi",'question': questions, 'answer': answers}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"sofi_faqs_{timestamp}.csv"

S3Utils.Upload(S3.S3_FAQ_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_FAQ_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")

driver.quit()
