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
    "https://www.ally.com/help/credit-cards/",
    "https://www.ally.com/help/about-ally/",
    "https://www.ally.com/help/careers/",
    "https://www.ally.com/help/investor-relations/",
    "https://www.ally.com/help/demand-notes/",
    "https://www.ally.com/help/press-room/",
    "https://www.ally.com/help/grants/",
    "https://www.ally.com/help/privacy-security/",
    "https://www.ally.com/help/bank/cds/",
    "https://www.ally.com/help/bank/cd-ladders/",
    "https://www.ally.com/help/bank/raise-your-rate/",
    "https://www.ally.com/help/bank/no-penalty-cd/",
    "https://www.ally.com/help/bank/savings-money-market/",
    "https://www.ally.com/help/bank/interest-checking/",
    "https://www.ally.com/help/bank/accounts-trust/",
    "https://www.ally.com/help/bank/iras/",
    "https://www.ally.com/help/bank/ira-hycd/",
    "https://www.ally.com/help/bank/ira-ryr/",
    "https://www.ally.com/help/bank/ira-osa/",
    "https://www.ally.com/help/bank/opening-account/",
    "https://www.ally.com/help/bank/account-information/",
    "https://www.ally.com/help/bank/login/",
    "https://www.ally.com/help/bank/beneficiaries/",
    "https://www.ally.com/help/bank/alerts-notifications/",
    "https://www.ally.com/help/bank/deposits/",
    "https://www.ally.com/help/bank/direct-deposit/",
    "https://www.ally.com/help/bank/early-direct-deposit/",
    "https://www.ally.com/help/bank/transfers/",
    "https://www.ally.com/help/bank/atms-withdrawals/",
    "https://www.ally.com/help/bank/debit-cards-checks/",
    "https://www.ally.com/help/bank/overdraft-protection/",
    "https://www.ally.com/help/bank/bill-pay/",
    "https://www.ally.com/help/bank/zelle/",
    "https://www.ally.com/help/bank/tax-documents/",
    "https://www.ally.com/help/invest/self-directed/",
    "https://www.ally.com/help/invest/robo-portfolio/",
    "https://www.ally.com/help/invest/wealth-management/",
    'https://www.ally.com/help/bank/savings-money-market/',
    "https://www.ally.com/help/home-loans/mortgage-get-started/",
    "https://www.ally.com/help/home-loans/mortgage-options/",
    "https://www.ally.com/help/home-loans/mortgage-preapproval/",
    "https://www.ally.com/help/home-loans/mortgage-application/",
    "https://www.ally.com/help/home-loans/mortgage-rates/",
    "https://www.ally.com/help/home-loans/mortgage-closing/",
    "https://www.ally.com/help/home-loans/refinance-get-started/",
    "https://www.ally.com/help/home-loans/refinance-application/",
    "https://www.ally.com/help/home-loans/refinance-rates/",
    "https://www.ally.com/help/home-loans/refinance-options/",
    "https://www.ally.com/help/home-loans/refinance-closing/",
    "https://www.ally.com/help/home-loans/general-support/",
    "https://www.ally.com/help/home-loans/escrow/",
    "https://www.ally.com/help/home-loans/forms/",
    "https://www.ally.com/help/home-loans/payments/",
    "https://www.ally.com/help/home-loans/insurance/",
    "https://www.ally.com/help/home-loans/payoff/",
    "https://www.ally.com/help/auto/personal-auto/",
    "https://www.ally.com/help/auto/vehicle-protection/",
    "https://www.ally.com/help/auto/auto-payment/",
    "https://www.ally.com/help/auto/pay-by-text/",
    "https://www.ally.com/help/auto/auto-payment-extension/",
    "https://www.ally.com/help/auto/auto-pay/",
    "https://www.ally.com/help/auto/auto-statements/",
    "https://www.ally.com/help/auto/auto-modification/",
    "https://www.ally.com/help/auto/scra/",
    "https://www.ally.com/help/auto/lease-end/",
    "https://www.ally.com/help/auto/auto-login/",
    "https://www.ally.com/help/auto/account-information/",
    "https://www.ally.com/help/auto/auto-contracts/",
    "https://www.ally.com/help/auto/manage-profile/",
    "https://www.ally.com/help/auto/online-activity/",
    "https://www.ally.com/help/auto/alerts/",
    "https://www.ally.com/help/auto/auto-payoff/",
    "https://www.ally.com/help/auto/message-center/",
    "https://www.ally.com/help/auto/documents/",
    "https://www.ally.com/help/auto/privacy-preferences/",
    "https://www.ally.com/help/auto/special-handling/"
    
]

questions = []
answers = []

for url in urls:
    try:
        driver.get(url) 
        time.sleep(3)  
        faq_list = driver.find_elements(By.CLASS_NAME, "allysf-faqs-v1-list-item")

        for faq in faq_list:
            try:
                question_element = faq.find_element(By.CLASS_NAME, "allysf-faqs-v1-trigger-text")
                question_inner_html = question_element.get_attribute("innerHTML")
                question_soup = BeautifulSoup(question_inner_html, "html.parser")
                question = question_soup.get_text(separator=" ").strip()

                answer_element = faq.find_element(By.CLASS_NAME, "allysf-faqs-v1-panel")
                answer_inner_html = answer_element.get_attribute("innerHTML")
                answer_soup = BeautifulSoup(answer_inner_html, "html.parser")
                answer = answer_soup.get_text(separator=" ").strip()

                if question and answer:
                    questions.append(question)
                    answers.append(answer)
            except Exception as faq_error:
                logger.error(f"Error processing FAQ on {url}: {faq_error}")
                continue
    except Exception as url_error:
        logger.error(f"Error accessing URL {url}: {url_error}")
        continue  

data = {'website':'ally','question': questions, 'answer': answers}
data_df = pd.DataFrame(data)

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')                                        
file_name = f"ally_faqs_{timestamp}.csv"

S3Utils.Upload(S3.S3_FAQ_DIRECTORY, file_name,data_df)
S3Utils.Upload(S3.S3_BACKUP_DIRECTORY, file_name,data_df)

logger.info(f"{file_name} uploaded into S3/{S3.S3_FAQ_DIRECTORY} and s3/{S3.S3_BACKUP_DIRECTORY} successfully ")
driver.quit()

