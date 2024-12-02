import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import logging
from datetime import datetime
from dateutil import parser
from pandas import DataFrame
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter

from Utils.S3Utils import S3Utils
from Utils.MongoUtils import MongoUtils

from Config.MongoDB import MongoDB
from Config.S3 import S3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def data_transformation(raw_data_df: DataFrame):
    try:
        required_columns = ['website', 'title', 'author', 'date', 'content', 'blog_url']
        for column in required_columns:
            if column not in raw_data_df.columns:
                raw_data_df[column] = None  
                
        raw_data_df['author'] = raw_data_df['author'].apply(lambda x: ''.join(re.findall(r'[A-Za-z]+', str(x))) if x else None)
        cleaned_data_df = raw_data_df.drop_duplicates(subset=['website', 'title', 'author', 'date', 'content', 'blog_url'])
        cleaned_data_df = cleaned_data_df.dropna(subset=['website', 'title', 'date', 'content', 'blog_url'])

        def parse_date(date_str):
            try:
                return parser.parse(date_str, fuzzy=True).date()
            except Exception as e:
                return None

        cleaned_data_df['date'] = cleaned_data_df['date'].apply(parse_date)
        cleaned_data_df = cleaned_data_df.dropna(subset=['date'])
        
        return cleaned_data_df
    except Exception as e:
        logger.error(f"Error during data transformation: {e}")
        raise

    
def chunk_text_with_langchain(data, chunk_size=1000, chunk_overlap=300):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " "],
        )

        chunks = []

        for _, row in data.iterrows():
            website = row["website"]
            blog_url = row["blog_url"]
            title = row["title"]
            author = row["author"]
            content = row["content"]

            content_chunks = text_splitter.split_text(content)

            for chunk in content_chunks:
                author = row["author"] if row["author"] else "Unknown"
                chunk_with_context = f"Website: {website}\nTitle: {title}\nAuthor: {author}\nDate: {row['date']}\nContent: {chunk}"

                chunks.append({
                    "website": website,
                    "blog_url":blog_url,
                    "title": title,
                    "author": author,
                    "blog_content": content,
                    "blog_date": datetime.combine(row['date'], datetime.min.time()),  
                    "chunk": chunk_with_context,
                    "is_embed": False,
                    "timestamp": datetime.now()
                })

        return DataFrame(chunks)
    except Exception as e:
        logger.error(f"Error during text chunking: {e}")
        raise


def insert_data_into_mongo():
    try:
        csv_files = S3Utils.list_csv_files_in_s3(S3.S3_BLOGS_DIRECTORY)
        logger.info(f"Found {len(csv_files)} files.")

        total_files_processed = 0
        mongoutils = MongoUtils()
        mongoutils.create_collection(MongoDB.BLOGS_COLLECTION)


        for file_key in csv_files:
            try:
                raw_data_df = S3Utils.read_file(file_key)
                transformed_data = data_transformation(raw_data_df)
                chunks = chunk_text_with_langchain(transformed_data)
                
                mongoutils.insert_items(MongoDB.BLOGS_COLLECTION, chunks)
                
                # S3Utils.delete_s3_file(file_key)

                total_files_processed += 1

            except Exception as e:
                logger.error(f"Failed to process {file_key}: {e}")

    except Exception as e:
        logger.error(e)

    logger.info(f"Total files processed: {total_files_processed}")

if __name__ == "__main__":
    logger.info(f"Starting script at {datetime.now()}")
    insert_data_into_mongo()
