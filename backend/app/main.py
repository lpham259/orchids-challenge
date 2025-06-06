from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Import models and services
from .models import (
    ScrapeRequest, GenerationJob, GenerationResponse, 
    JobStatusResponse, JobStatus, ScrapedData
)
from app.scraper import WebsiteScraper
from app.llm_generator import LLMGenerator

# Create FastAPI instance
app = FastAPI(
    title="Website Cloner API",
    description="API for scraping websites and generating HTML clones using LLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs (in production, use a database)
jobs_db: Dict[str, GenerationJob] = {}

# Initialize LLM service
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not LLM_API_KEY:
    print("Warning: No LLM API key found.")

llm_generator = LLMGenerator(provider=LLM_PROVIDER, api_key=LLM_API_KEY) if LLM_API_KEY else None

@app.get("/")
async def root():
    return {
        "message": "Website Cloner API", 
        "status": "running",
        "endpoints": {
            "start_cloning": "POST /clone",
            "check_status": "GET /status/{job_id}",
            "get_result": "GET /result/{job_id}",
            "list_jobs": "GET /jobs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "website-cloner-api",
        "scraper_available": True,
        "llm_configured": llm_generator is not None,
        "llm_provider": LLM_PROVIDER if llm_generator else None
    }

@app.post("/clone", response_model=GenerationResponse)
async def start_website_cloning(
    request: ScrapeRequest, 
    background_tasks: BackgroundTasks
):
    """Start the website cloning process"""
    
    # Create new job
    job = GenerationJob(url=str(request.url))
    jobs_db[job.id] = job
    
    # Start background processing
    background_tasks.add_task(process_website_cloning, job.id, request)
    
    return GenerationResponse(
        job_id=job.id,
        status=job.status,
        message=f"Website cloning started. {'LLM Generation enabled.' if llm_generator else 'Using fallback mode - set ANTHROPIC_API_KEY for AI generation.'}"
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a cloning job"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    # Calculate progress based on status
    progress_map = {
        JobStatus.PENDING: 0,
        JobStatus.SCRAPING: 25,
        JobStatus.PROCESSING: 50,
        JobStatus.GENERATING: 75,
        JobStatus.COMPLETED: 100,
        JobStatus.FAILED: 0
    }
    
    return JobStatusResponse(
        id=job.id,
        url=job.url,
        status=job.status,
        progress=progress_map.get(job.status, 0),
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """Get the generated HTML result"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Job not completed. Current status: {job.status}"
        )
    
    if not job.generated_html:
        raise HTTPException(status_code=404, detail="Generated HTML not found")
    
    return {
        "job_id": job.id,
        "url": job.url,
        "generated_html": job.generated_html,
        "scraped_data": job.scraped_data.dict() if job.scraped_data else None,
        "created_at": job.created_at,
        "completed_at": job.updated_at
    }

@app.get("/result/{job_id}/preview", response_class=HTMLResponse)
async def preview_result(job_id: str):
    """Preview the generated HTML in browser"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job.status != JobStatus.COMPLETED or not job.generated_html:
        return HTMLResponse(
            content="<html><body><h1>Result not ready</h1><p>Job not completed or HTML not generated yet.</p></body></html>",
            status_code=404
        )
    
    return HTMLResponse(content=job.generated_html)

@app.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    """List all jobs"""
    
    job_list = []
    for job in jobs_db.values():
        progress_map = {
            JobStatus.PENDING: 0,
            JobStatus.SCRAPING: 25,
            JobStatus.PROCESSING: 50,
            JobStatus.GENERATING: 75,
            JobStatus.COMPLETED: 100,
            JobStatus.FAILED: 0
        }
        
        job_list.append(JobStatusResponse(
            id=job.id,
            url=job.url,
            status=job.status,
            progress=progress_map.get(job.status, 0),
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        ))
    
    # Sort by creation time, newest first
    job_list.sort(key=lambda x: x.created_at, reverse=True)
    return job_list

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs_db[job_id]
    return {"message": f"Job {job_id} deleted successfully"}

# Background task functions
async def process_website_cloning(job_id: str, request: ScrapeRequest):
    """Background task to process website cloning"""
    
    job = jobs_db[job_id]
    
    try:
        # Step 1: Update status to scraping
        job.status = JobStatus.SCRAPING
        job.updated_at = datetime.now()
        
        # Step 2: Scrape the website using enhanced scraper
        async with WebsiteScraper() as scraper:
            scraped_data_dict = await scraper.scrape_website(str(request.url))
            job.scraped_data = ScrapedData(**scraped_data_dict)
        
        # Step 3: Update status to processing
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now()
        
        # Small delay to show progress
        await asyncio.sleep(1)
        
        # Step 4: Update status to generating (for now, we'll create basic HTML)
        job.status = JobStatus.GENERATING
        job.updated_at = datetime.now()
        
        # Step 5: Generate HTML using LLM or fallback
        if llm_generator:
            print(f"Using LLM generation for job {job_id}")
            generated_html = await llm_generator.generate_html_clone(scraped_data_dict)
            job.generated_html = generated_html
        else:
            print(f"Using fallback generation for job {job_id} (no LLM configured)")
            job.generated_html = _create_enhanced_html(job.scraped_data)
        
        # Step 6: Mark as completed
        job.status = JobStatus.COMPLETED
        job.updated_at = datetime.now()
        
    except Exception as e:
        # Handle errors
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.updated_at = datetime.now()
        print(f"Error processing job {job_id}: {e}")

def _create_enhanced_html(scraped_data: ScrapedData) -> str:
    """Create enhanced HTML from scraped data (placeholder for LLM integration)"""
    
    title = scraped_data.title or "Cloned Website"
    colors = scraped_data.color_palette[:5] if scraped_data.color_palette else ["#333333", "#ffffff", "#007bff"]
    fonts = scraped_data.fonts[:3] if scraped_data.fonts else ["Arial", "sans-serif"]
    
    # Use extracted colors and fonts in the generated HTML
    primary_color = colors[0] if colors else "#333333"
    bg_color = colors[1] if len(colors) > 1 else "#ffffff"
    accent_color = colors[2] if len(colors) > 2 else "#007bff"
    primary_font = fonts[0] if fonts else "Arial, sans-serif"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: {primary_font};
            margin: 0;
            padding: 0;
            background-color: {bg_color};
            color: {primary_color};
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: {primary_color};
            color: {bg_color};
            padding: 2rem 0;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .content {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .color-palette {{
            display: flex;
            gap: 10px;
            margin: 1rem 0;
        }}
        .color-swatch {{
            width: 40px;
            height: 40px;
            border-radius: 4px;
            border: 2px solid #ddd;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid {accent_color};
        }}
        .font-preview {{
            font-family: {primary_font};
            font-size: 1.2em;
            margin: 0.5rem 0;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <p>Enhanced clone with extracted design data</p>
        </div>
    </header>
    
    <main class="container">
        <div class="content">
            <h2>🎨 Extracted Design Elements</h2>
            
            <div class="info-grid">
                <div class="info-card">
                    <h3>📱 Original URL</h3>
                    <p><a href="{scraped_data.url}" target="_blank">{scraped_data.url}</a></p>
                </div>
                
                <div class="info-card">
                    <h3>🎨 Color Palette</h3>
                    <div class="color-palette">
                        {"".join([f'<div class="color-swatch" style="background-color: {color}" title="{color}"></div>' for color in colors[:6]])}
                    </div>
                    <p>Found {len(scraped_data.color_palette or [])} colors</p>
                </div>
                
                <div class="info-card">
                    <h3>🔤 Typography</h3>
                    {"".join([f'<div class="font-preview" style="font-family: {font}">{font}</div>' for font in fonts[:3]])}
                    <p>Found {len(scraped_data.fonts or [])} font families</p>
                </div>
                
                <div class="info-card">
                    <h3>📊 Page Structure</h3>
                    <p>DOM elements analyzed</p>
                    <p>Layout information extracted</p>
                    <p>Styles computed</p>
                </div>
            </div>
            
            <div style="margin-top: 2rem; padding: 1rem; background: #e3f2fd; border-radius: 6px;">
                <h3>🤖 Next Step: LLM Integration</h3>
                <p>This enhanced HTML uses the extracted colors, fonts, and structure data. 
                   In the next phase, we'll integrate an LLM to generate pixel-perfect recreations!</p>
            </div>
        </div>
    </main>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)