import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams
import openai

from Utils.MongoUtils import MongoUtils
from Config.OpenAI import OpenAI
from Config.MongoDB import MongoDB
from Config.Qdrant import Qdrant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OpenAI.API_KEY
qdrant_client = QdrantClient(
    url=Qdrant.QDRANT_URL, 
    api_key=Qdrant.QDRANT_API_KEY,
    timeout=100
)

def initialize_qdrant_collection(vector_size):
    collection_exists = qdrant_client.collection_exists(collection_name=Qdrant.QDRANT_COLLECTION)
    
    if collection_exists:
        logger.info(f"Collection '{Qdrant.QDRANT_COLLECTION}' already exists.")
    else:
        qdrant_client.create_collection(
            collection_name=Qdrant.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance="Cosine"),
        )
        logger.info(f"Collection '{Qdrant.QDRANT_COLLECTION}' created.")

def generate_embeddings(documents):
    embeddings = []
    for doc in documents:
        chunk = doc.get("chunk")
        if chunk:
            try:
                response = openai.Embedding.create(input=chunk, model=OpenAI.MODEL_NAME_EMBEDDING)
                embeddings.append({
                    "text": chunk,
                    "embedding": response["data"][0]["embedding"],
                    "document": doc  
                })
            except Exception as e:
                logger.error(f"Error generating embedding for chunk: {chunk}. Error: {e}")
        else:
            logger.warning(f"Document with ID {doc['_id']} has no content to generate embedding.")
    return embeddings

def batch_upsert_embeddings(embeddings, batch_size=100):
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        points = []
        for idx, embedding in enumerate(batch):
            doc = embedding["document"]
            payload = {key: value for key, value in doc.items() if key != '_id'}
            
            point = PointStruct(
                id=idx,
                vector=embedding["embedding"],
                payload={
                    "text": embedding["text"],  
                    **payload, 
                },
            )
            points.append(point)

        qdrant_client.upsert(collection_name=Qdrant.QDRANT_COLLECTION, points=points)

def update_mongo_with_embeddings(mongoutils, embeddings):

    bulk_updates = [] 

    for embedding in embeddings:
        bulk_updates.append({
            'filter': {'_id': embedding["document"]['_id']},
            'update_fields': {'is_embed': True}
        })

    result = mongoutils.bulk_update_documents(
        collection=MongoDB.FAQ_COLLECTION,
        updates=bulk_updates
    )
    logger.info(f"Successfully updated {result} documents in MongoDB.")
    
if __name__ == "__main__":
    try:
        mongoutils = MongoUtils()

        documents = mongoutils.query_collection(
            collection=MongoDB.FAQ_COLLECTION,
            filters=[{"is_embed": False}],
            selected_fields=["_id","website","question","chunk","answer"]
        )

        if not documents:
            logger.info("No data found in MongoDB.")
        else:
            embeddings = generate_embeddings(documents)

            if embeddings:
                vector_size = len(embeddings[0]["embedding"])
                initialize_qdrant_collection(vector_size)

                batch_upsert_embeddings(embeddings)

                update_mongo_with_embeddings(mongoutils, embeddings)

            else:
                logger.info("No embeddings generated. Skipping Qdrant storage.")
                
    except Exception as e:
        logger.error(f"An error occurred: {e}")
