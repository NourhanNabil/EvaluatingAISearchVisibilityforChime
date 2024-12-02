from fastapi import APIRouter, HTTPException
import logging
import openai
import re
from qdrant_client import QdrantClient
from typing import List, Dict

from datasets import Dataset
from pandas import DataFrame

from Definitions.ChatResponse import ChatResponse
from Definitions.QueryRequest import QueryRequest

from Config.OpenAI import OpenAI
from Config.Qdrant import Qdrant

from urllib.parse import urlparse
from ragas import evaluate
from ragas.metrics import (
        answer_relevancy,
        context_precision,
        faithfulness
    )


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
            '''  You are a specialist in digital banking services. Your task is to generate technical content based on a user query given a specific context.
    
                Here is a list of steps that you need to follow in order to solve this task:
                Step 1: You need to analyze the user provided query : {question}
                Step 2: You need to analyze the provided context and how the information in it relates to the user question: {context}
                Step 3: Generate the content keeping in mind that it needs to be as cohesive and concise as possible related to the subject presented in the query.
                
                Reply without justifying the context that you are given  
    '''},
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

def evaluate_w_ragas(query: str, context: List[str], output: str) -> DataFrame:
    eval_data = {
        "question": [query],
        "answer": [output],
        "contexts": [[context]], 
        "ground_truth": [context],  
    }
    
    dataset = Dataset.from_dict(eval_data)  

    metrics = [answer_relevancy, context_precision, faithfulness]

    result = evaluate(dataset=dataset, metrics=metrics)
    result_dataframe = DataFrame(result.scores, index=[0])  

    metrics_dict = {
        "answer_relevancy": round(result_dataframe["answer_relevancy"][0],2),
        "faithfulness": round(result_dataframe["faithfulness"][0],2)
    }
    
    return metrics_dict

def extract_backlinks(text: str) -> list:
    urls = re.findall(r'https?://[^\s]+', text)
    return urls

def evaluate_backlinks(urls: list) -> float:
    trusted_domains = ["ally.com", "chime.com","capitalone.com","sofi.com","varomoney.com"]
    score = 0
    for url in urls:
        domain = urlparse(url).netloc
        if domain in trusted_domains:
            score += 0.5  
    return score

def detect_brand_mentions(text: str, brand_names: list) -> int:
    mentions = 0
    for brand in brand_names:
        if re.search(r'\b' + re.escape(brand) + r'\b', text, re.IGNORECASE):
            mentions += 1
    return mentions

def evaluate_authority_signals(text: str, brand_names: list) -> Dict[str, float]:
    urls = extract_backlinks(text)
    backlinks_score = evaluate_backlinks(urls)

    brand_mentions = detect_brand_mentions(text, brand_names)

    total_score = backlinks_score + brand_mentions * 0.5 

    return {
        "backlinks_score": round(backlinks_score, 2),
        "brand_mentions_score": brand_mentions,
        "total_authority_score": round(total_score, 2)
    }

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
    evaluation_score = evaluate_w_ragas(query=query, context=context, output=response_text)
    brand_names = ["chime", "capital one","ally","varo","sofi"]

    authority_signals = evaluate_authority_signals(response_text, brand_names)

    return ChatResponse(
        response=response_text, 
        evaluation_score=evaluation_score,
        authority_score=authority_signals
    )
    