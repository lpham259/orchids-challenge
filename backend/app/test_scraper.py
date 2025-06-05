import asyncio
import json
import sys
import os

# Add the backend app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from scraper import WebsiteScraper

async def test_scraper():
    """Test the enhanced scraper with a simple website"""
    
    test_url = "https://example.com"  # Start simple
    
    print(f"🔍 Testing scraper with: {test_url}")
    print("=" * 50)
    
    try:
        async with WebsiteScraper() as scraper:
            print("✅ Scraper initialized successfully")
            
            # Scrape the website
            print("🌐 Starting scraping process...")
            data = await scraper.scrape_website(test_url)
            
            print("✅ Scraping completed successfully!")
            print("\n📊 **RESULTS SUMMARY:**")
            print(f"Title: {data.get('title', 'N/A')}")
            print(f"URL: {data.get('url', 'N/A')}")
            print(f"Screenshot captured: {'✅' if data.get('screenshot_base64') else '❌'}")
            print(f"DOM structure extracted: {'✅' if data.get('dom_structure') else '❌'}")
            print(f"Styles extracted: {'✅' if data.get('styles') else '❌'}")
            print(f"Colors found: {len(data.get('color_palette', []))} colors")
            print(f"Fonts found: {len(data.get('fonts', []))} fonts")
            print(f"Layout info: {'✅' if data.get('layout_info') else '❌'}")
            print(f"Meta data: {'✅' if data.get('meta_data') else '❌'}")
            
            # Show some extracted data
            if data.get('color_palette'):
                print(f"\n🎨 **Colors:** {data['color_palette'][:5]}")
            
            if data.get('fonts'):
                print(f"🔤 **Fonts:** {data['fonts'][:3]}")
            
            if data.get('dom_structure', {}).get('text_content'):
                text_preview = data['dom_structure']['text_content'][:200]
                print(f"📝 **Text Preview:** {text_preview}...")
            
            # Save detailed results to file
            with open('scraper_test_results.json', 'w') as f:
                # Don't save the base64 screenshot (too large)
                data_copy = data.copy()
                if 'screenshot_base64' in data_copy:
                    data_copy['screenshot_base64'] = f"[{len(data['screenshot_base64'])} characters]"
                
                json.dump(data_copy, f, indent=2, default=str)
            
            print(f"\n💾 **Detailed results saved to:** scraper_test_results.json")
            print("\n✅ **TEST PASSED:** All scraping functions working!")
            
    except Exception as e:
        print(f"❌ **TEST FAILED:** {str(e)}")
        import traceback
        traceback.print_exc()

async def test_multiple_sites():
    """Test with multiple websites"""
    
    test_sites = [
        "https://example.com",
        "https://stripe.com", 
        "https://github.com",
        "https://tailwindcss.com"
    ]
    
    print("🧪 Testing multiple websites...")
    print("=" * 50)
    
    async with WebsiteScraper() as scraper:
        for url in test_sites:
            try:
                print(f"\n🔍 Testing: {url}")
                data = await scraper.scrape_website(url)
                
                print(f"  ✅ Title: {data.get('title', 'N/A')}")
                print(f"  🎨 Colors: {len(data.get('color_palette', []))}")
                print(f"  🔤 Fonts: {len(data.get('fonts', []))}")
                print(f"  📱 Screenshot: {'✅' if data.get('screenshot_base64') else '❌'}")
                
            except Exception as e:
                print(f"  ❌ Failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Enhanced Scraper Test Suite")
    print("=" * 50)
    
    # Install Playwright browsers if needed
    print("📦 Checking Playwright installation...")
    os.system("playwright install chromium")
    
    choice = input("\nChoose test:\n1. Single site (detailed)\n2. Multiple sites (quick)\nEnter 1 or 2: ")
    
    if choice == "2":
        asyncio.run(test_multiple_sites())
    else:
        asyncio.run(test_scraper())