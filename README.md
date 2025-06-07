# Website Cloner

AI-powered website cloning tool that generates HTML replicas from any website URL using PDF analysis and Claude AI.

## Features

-  **AI-Powered Cloning** - Uses Claude Sonnet 4 to generate HTML from website visuals
-  **PDF Analysis** - Captures complete scrollable pages as PDFs for comprehensive analysis
-  **Anti-Bot Detection** - Optional Hyperbrowser integration for stealth scraping
-  **Visual Analysis** - Screenshot capture and color palette extraction
-  **Real-time Progress** - Live job tracking with WebSocket-like polling
-  **Modern UI** - Clean React frontend with preview and download capabilities

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+ and pip
- **Anthropic API Key** ([Get one here](https://console.anthropic.com/))
- **Hyperbrowser API Key** (Optional, [Get one here](https://hyperbrowser.ai/))

## Quick Start

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd website-cloner
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Configuration
Create `.env` file in the backend directory:
```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for better success rates)
HYPERBROWSER_API_KEY=your_hyperbrowser_api_key_here
BROWSER_PROVIDER=hyperbrowser  # or "local"

# LLM Configuration
LLM_PROVIDER=anthropic
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

### 5. Start Services
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### 6. Open Application
Visit [http://localhost:3000](http://localhost:3000)

## Usage

1. **Enter URL** - Paste any publicly accessible website URL
2. **Start Cloning** - Click "Clone Website" to begin AI analysis
3. **Monitor Progress** - Watch real-time progress through scraping → processing → generating phases
4. **View Results** - Preview the generated HTML clone in the browser
5. **Download** - Save the HTML file for use anywhere

### Example URLs to Try
- `stripe.com` - Clean design, good for testing
- `vercel.com` - Modern layout with gradients
- `github.com` - Complex interface with lots of components
- `tailwindcss.com` - Documentation site with multiple sections

## API Configuration

### Required: Anthropic API Key
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Create account and generate API key
3. Add to `.env` as `ANTHROPIC_API_KEY=your_key_here`

### Optional: Hyperbrowser API Key
**Why use Hyperbrowser?**
- Bypass anti-bot detection (Cloudflare, etc.)
- Better success rates on protected sites
- Stealth mode and automatic CAPTCHA solving
- 30 hours free tier (vs 1 hour local browser time)

**Setup:**
1. Visit [hyperbrowser.ai](https://hyperbrowser.ai/)
2. Sign up for free account (3,000 credits = ~30 hours)
3. Generate API key from dashboard
4. Add to `.env` as `HYPERBROWSER_API_KEY=your_key_here`
5. Set `BROWSER_PROVIDER=hyperbrowser`

## How It Works

1. **Scraping** - Captures website screenshot and generates PDF of full page
2. **Processing** - Extracts colors, fonts, layout info, and DOM structure  
3. **AI Generation** - Claude analyzes PDF/screenshots and generates matching HTML
4. **Optimization** - Cleans and formats the generated code

## Requirements

### Backend Dependencies
```
fastapi>=0.104.0
uvicorn>=0.24.0
playwright>=1.40.0
anthropic>=0.7.0
hyperbrowser>=0.1.0
beautifulsoup4>=4.12.0
colorthief>=0.2.1
Pillow>=10.0.0
python-dotenv>=1.0.0
pydantic>=2.5.0
```

### Frontend Dependencies
- React 18+
- Next.js 14+
- Tailwind CSS
- TypeScript

## Troubleshooting

### Common Issues

**"No LLM API key found"**
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Restart backend after adding keys

**"Hyperbrowser connection failed"**
- Check `HYPERBROWSER_API_KEY` is correct
- Will automatically fallback to local browser
- Set `BROWSER_PROVIDER=local` to skip Hyperbrowser

**Website timeouts**
- Some sites block automation (Asos, Hilton, etc.)
- Try enabling Hyperbrowser for better success rates
- Increase timeout in scraper settings

**Preview not scrollable**
- Updated iframe sandbox settings should fix this
- Try refreshing the preview or opening in new tab

### Performance Tips

- Use Hyperbrowser for complex/protected sites
- Start with simple sites to test setup
- Check debug endpoints: `/debug/{job_id}/keys` for troubleshooting

## API Endpoints

- `POST /clone` - Start website cloning job
- `GET /status/{job_id}` - Check job progress
- `GET /result/{job_id}` - Get generated HTML
- `GET /result/{job_id}/preview` - Preview in browser
- `GET /jobs` - List all jobs
- `DELETE /jobs/{job_id}` - Delete job

## Development

### Backend Structure
```
backend/
├── app/
│   ├── main.py           # FastAPI server
│   ├── models.py         # Pydantic models
│   ├── scraper.py        # Website scraping logic
│   └── llm_generator.py  # AI HTML generation
└── requirements.txt
```

### Frontend Structure  
```
frontend/
├── src/
│   ├── app/
│   │   ├── components/   # React components
│   │   └── page.tsx      # Main application
│   └── ...
└── package.json
```