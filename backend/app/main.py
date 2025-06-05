from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ScrapeRequest, ScrapeResponse

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
    # Placeholder - returns dummy HTML
    dummy_html = f"""<!DOCTYPE html>
<html>
<head><title>Cloned: {request.url}</title></head>
<body>
    <h1>MVP Clone of {request.url}</h1>
    <p>This is a placeholder. Real cloning coming soon!</p>
</body>
</html>"""
    
    return ScrapeResponse(
        success=True,
        message="MVP clone completed",
        html=dummy_html
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)