from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ScrapeRequest, ScrapeResponse
from .scraper import scrape_website_basic

app = FastAPI(title="Website Cloner MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Website Cloner MVP"}

@app.post("/clone", response_model=ScrapeResponse)
async def clone_website(request: ScrapeRequest):
    try:
        html_content = await scrape_website_basic(request.url)
        return ScrapeResponse(
            success=True,
            message="Website scraped successfully",
            html=html_content
        )
    except Exception as e:
        return ScrapeResponse(
            success=False,
            message=f"Error: {str(e)}",
            html=None
        )
    
    return ScrapeResponse(
        success=True,
        message="MVP clone completed",
        html=dummy_html
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)