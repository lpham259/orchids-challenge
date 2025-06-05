from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
from datetime import datetime

class JobStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapeRequest(BaseModel):
    url: HttpUrl
    include_screenshots: bool = True
    include_dom: bool = True
    include_styles: bool = True

class ScrapedData(BaseModel):
    url: str
    title: Optional[str] = None
    screenshot_base64: Optional[str] = None
    dom_structure: Optional[Dict[str, Any]] = None
    styles: Optional[Dict[str, Any]] = None
    color_palette: Optional[List[str]] = None
    fonts: Optional[List[str]] = None
    layout_info: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None

class GenerationJob(BaseModel):
    id: str = None
    url: str
    status: JobStatus = JobStatus.PENDING
    scraped_data: Optional[ScrapedData] = None
    generated_html: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('created_at'):
            data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        super().__init__(**data)

class GenerationResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str

class JobStatusResponse(BaseModel):
    id: str
    url: str
    status: JobStatus
    progress: int  # 0-100
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime