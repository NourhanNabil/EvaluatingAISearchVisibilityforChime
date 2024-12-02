import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import logging
from datetime import datetime
from pandas import DataFrame
from langchain.text_splitter import RecursiveCharacterTextSplitter  

from Utils.S3Utils import S3Utils
from Utils.MongoUtils import MongoUtils

from Config.MongoDB import MongoDB
from Config.S3 import S3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def data_transformation(raw_data_df: DataFrame):
    try:
        cleaned_data_df = raw_data_df.drop_duplicates(subset=['website', 'question', 'answer'])
        cleaned_data_df = cleaned_data_df.dropna(subset=['website', 'question', 'answer'])
        
        
        return cleaned_data_df
    except Exception as e:
        logger.error(f"Error during data transformation: {e}")
        raise


def chunk_text_with_langchain(data, chunk_size=1000, chunk_overlap=300):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )
    
    chunks = []
    
    for _, row in data.iterrows():
        website = row.get("website")
        question = row.get("question", "")
        answer = row.get("answer", "")
        
        answer_chunks = text_splitter.split_text(answer)
        
        for chunk in answer_chunks:
            combined_chunk = f"website: {website}\nQ: {question}\nA: {chunk}"
            
            chunks.append({
                "website": website,
                "question": question,
                "answer": answer,
                "chunk": combined_chunk,
                "is_embed": False,
                "timestamp": datetime.now()
            })
    
    return DataFrame(chunks)


def insert_data_into_mongo():
    try:
        csv_files = S3Utils.list_csv_files_in_s3(S3.S3_FAQ_DIRECTORY)
        logger.info(f"Found {len(csv_files)} files.")
        
        total_files_processed = 0
        mongoutils = MongoUtils()
        mongoutils.create_collection(MongoDB.FAQ_COLLECTION)

        for file_key in csv_files:
            try:
                raw_data_df = S3Utils.read_file(file_key)                
                transformed_data = data_transformation(raw_data_df)
                chunks = chunk_text_with_langchain(transformed_data)
                mongoutils.insert_items(MongoDB.FAQ_COLLECTION, chunks)
                
                total_files_processed += 1

                # S3Utils.delete_s3_file(file_key)

            except Exception as e:
                logger.error(f"Failed to process {file_key}: {e}")
                        
    except Exception as e:
        logger.error(e)

    logger.info(f"Total files processed: {total_files_processed}")

if __name__ == "__main__":
    logger.info(f"Starting script at {datetime.now()}")
    insert_data_into_mongo()
