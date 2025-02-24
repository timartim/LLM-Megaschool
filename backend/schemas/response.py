
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

class PredictionResponse(BaseModel):
    id: int
    answer: Optional[int] = None
    reasoning: str
    sources: List[HttpUrl]