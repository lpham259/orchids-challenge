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

@app.post("/test-scraper")
async def test_scraper_endpoint(url: str = "https://example.com"):
    """Test endpoint to verify enhanced scraper works"""
    
    try:
        async with WebsiteScraper() as scraper:
            scraped_data = await scraper.scrape_website(url)
            
            # Return summary (don't return base64 screenshot in response)
            return {
                "success": True,
                "url": scraped_data.get("url"),
                "title": scraped_data.get("title"),
                "colors_found": len(scraped_data.get("color_palette", [])),
                "fonts_found": len(scraped_data.get("fonts", [])),
                "has_screenshot": bool(scraped_data.get("screenshot_base64")),
                "has_dom_structure": bool(scraped_data.get("dom_structure")),
                "has_styles": bool(scraped_data.get("styles")),
                "has_layout_info": bool(scraped_data.get("layout_info")),
                "text_content_length": len(scraped_data.get("dom_structure", {}).get("text_content", "")),
                "sample_colors": scraped_data.get("color_palette", [])[:5],
                "sample_fonts": scraped_data.get("fonts", [])[:3]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)