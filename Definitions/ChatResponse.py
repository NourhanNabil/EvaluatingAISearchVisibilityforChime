from pydantic import BaseModel
from typing import Optional, Dict


class ChatResponse(BaseModel):
    response: str
    evaluation_score: Optional[Dict[str, float]] = None 
    authority_score: Optional[Dict[str, float]] = None 