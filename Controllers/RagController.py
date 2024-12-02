from fastapi import APIRouter, HTTPException
import logging
import openai
from qdrant_client import QdrantClient
from typing import List, Dict

from Definitions.ChatResponse import ChatResponse
from Definitions.QueryRequest import QueryRequest

from Config.OpenAI import OpenAI
from Config.Qdrant import Qdrant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OpenAI.API_KEY

qdrant_client = QdrantClient(
    url=Qdrant.QDRANT_URL,
    api_key=Qdrant.QDRANT_API_KEY,
)

rag_router = APIRouter()


def generate_embedding(text: str) -> List[float]:
    try:
        response = openai.Embedding.create(input=text, model=OpenAI.MODEL_NAME_EMBEDDING)
        return response['data'][0]['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding for query: {text}. Error: {e}")
        return []

def search_qdrant(query_embedding: List[float], top_k: int = 10) -> List[Dict]:
    try:
        search_result = qdrant_client.search(
            collection_name=Qdrant.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        return [hit.payload for hit in search_result]
    except Exception as e:
        logger.error(f"Error searching Qdrant: {e}")
        return []

def generate_response(context: str, query: str) -> str:
    messages = [
        {"role": "system", "content": 
            '''You are an AI assistant trained to answer questions using the provided context. 
                                Response with No'''},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
    ]
    try:
        response = openai.ChatCompletion.create(
            model=OpenAI.MODEL_NAME,
            messages=messages,
            max_tokens=600,
            temperature=0
        )
        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        logger.error(f"Error generating response with GPT-4: {e}")
        return "Sorry, I couldn't generate an answer at the moment."

@rag_router.post("/chat", response_model=ChatResponse)
async def chat(query_request: QueryRequest):
    query = query_request.query

    query_embedding = generate_embedding(query)
    if not query_embedding:
        raise HTTPException(status_code=500, detail="Error generating query embedding.")

    results = search_qdrant(query_embedding)
    if not results:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join([doc.get('text', 'No content available') for doc in results])

    response_text = generate_response(context, query)

    return ChatResponse(response=response_text)

