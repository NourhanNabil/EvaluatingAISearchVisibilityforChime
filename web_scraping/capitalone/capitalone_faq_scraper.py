import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import logging

from Utils.S3Utils import S3Utils

from Config.S3 import S3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

urls = [
    'https://www.capitalone.com/credit-cards/faq/',
    'https://www.capitalone.com/auto-financing/faq/'
]

questions = []
answers = []

for url in urls:
    driver.get(url)

    time.sleep(3)

    try:
        tabs = driver.find_elements(By.CLASS_NAME, "grv-shr-lib-tabpanel__tab.tab-title")
    except Exception as e:
        logger.error(f"Error locating tabs on {url}: {e}")
        continue

    for tab in tabs:
        try:
            tab.click()
            time.sleep(2) 
            try:
                show_more_button = driver.find_element(By.CLASS_NAME, "show-more-button.ng-star-inserted")
                show_more_button.click()
                time.sleep(2) 
            except Exception:
                continue

            faq_list = driver.find_elements(By.TAG_NAME, "shared-accordion-item")

            for faq in faq_list:
                try:
                    question_element = faq.find_element(By.CLASS_NAME, "grv-shr-lib-accordion__heading")
                    question_inner_html = question_element.get_attribute("innerHTML")
                    question_soup = BeautifulSoup(question_inner_html, "html.parser")
                    question = question_soup.get_text(separator=" ").strip()

                    answer_element = faq.find_element(By.CLASS_NAME, "grv-shr-lib-padding__left--small")
                    answer_inner_html = answer_element.get_attribute("innerHTML")
                    answer_soup = BeautifulSoup(answer_inner_html, "html.parser")
                    answer = answer_soup.get_text(separator=" ").strip()

                    if question and answer:
                        questions.append(question)
                        answers.append(answer)
                except Exception as faq_error:
                    logger.error(f"Error processing FAQ: {faq_error}")
                    continue
        except Exception as tab_error:
            logger.error(f"Error processing tab: {tab_error}")
            continue

data = {'website':'capital one','question': questions, 'answer': answers}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"capitalone_faq_{timestamp}.csv"

S3Utils.Upload(S3.S3_FAQ_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_FAQ_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")

driver.quit()

