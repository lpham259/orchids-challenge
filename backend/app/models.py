from pydantic import BaseModel
from typing import Optional

class ScrapeRequest(BaseModel):
    url: str

class ScrapeResponse(BaseModel):
    success: bool
    message: str
    html: Optional[str] = None