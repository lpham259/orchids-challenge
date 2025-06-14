# backend/app/services/scraper.py
import asyncio
import base64
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page
import colorthief
from PIL import Image
import io
from bs4 import BeautifulSoup, Comment
import os

class WebsiteScraper:
    def __init__(self, headless: bool = True, provider: str = "local", api_key: str = None):
        self.headless = headless
        self.provider = provider
        self.api_key = api_key or os.getenv("HYPERBROWSER_API_KEY")
        self.browser: Optional[Browser] = None
        self.hb_client = None
        self.hb_session = None
        
    async def __aenter__(self):
        if self.provider == "hyperbrowser" and self.api_key:
            try:
                from hyperbrowser import AsyncHyperbrowser
                from hyperbrowser.models import CreateSessionParams

                print(f"Using Hyperbrowser with API key: {self.api_key[:8]}...")

                self.hb_client = AsyncHyperbrowser(api_key=self.api_key)
                print("Hyperbrowser client created")

                self.hb_session = await self.hb_client.sessions.create(
                    params=CreateSessionParams(
                        use_stealth = True,
                        adblock = True
                    )
                )
                print(f"🌐 Connected to Hyperbrowser session: {self.hb_session.id}")

                # Connect via CDP
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(self.hb_session.ws_endpoint)
            except ImportError:
                print("Hyperbrowser SDK not installed, falling back to local")
                self.provider = "local"
            except Exception as e:
                print(f"Hyperbrowser connection failed: {e}, falling back to local")
                self.provider = "local"

        if self.provider == "local":
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)

        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Clean up Hyperbrowser session
        if self.hb_client and self.hb_session:
            try:
                await self.hb_client.sessions.stop(self.hb_session.id)
                print("Hyperbrowser session cleaned up")
            except Exception as e:
                print(f"Error cleaning up Hyperbrowser session: {e}")

    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """Complete website scraping with PDF and screenshot capture"""
        if self.provider == "hyperbrowser":
            context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
            page = await context.new_page()
        else:
            page = await self.browser.new_page()
        
        try:
            print(f"🌐 Scraping: {url}")
            
            # Navigate to the page
            await page.goto(str(url), wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Let dynamic content load
            
            # Set optimal viewport for desktop
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
            # Capture visual data
            print("📸 Capturing full-page screenshots...")
            full_page_screenshots = await self._take_full_page_screenshots(page)
            
            print("📄 Generating full page PDF...")
            pdf_base64 = await self._generate_page_pdf(page)
            
            # Extract other data
            print("🔍 Extracting page data...")
            scraped_data = {
                "url": str(url),
                "title": await page.title(),
                "screenshot_base64": full_page_screenshots[0] if full_page_screenshots else "",
                "full_page_screenshots": full_page_screenshots,
                "screenshot_count": len(full_page_screenshots),
                "pdf_base64": pdf_base64,
                "dom_structure": await self._extract_dom_structure(page),
                "styles": await self._extract_styles(page),
                "color_palette": await self._extract_color_palette(page),
                "fonts": await self._extract_fonts(page),
                "layout_info": await self._extract_layout_info(page),
                "meta_data": await self._extract_meta_data(page)
            }
            
            print(f"✅ Scraping complete:")
            print(f"   📸 Screenshot: {'✅' if full_page_screenshots[0] else '❌'}")
            print(f"   📄 PDF: {'✅' if pdf_base64 else '❌'}")
            print(f"   🎨 Colors: {len(scraped_data.get('color_palette', []))}")
            print(f"   🔤 Fonts: {len(scraped_data.get('fonts', []))}")
            
            return scraped_data
            
        except Exception as e:
            raise Exception(f"Failed to scrape website: {str(e)}")
        finally:
            await page.close()

    async def _take_full_page_screenshots(self, page: Page) -> List[str]:
        """Take multiple screenshots covering the entire page height"""
        try:
            print("📸 Taking full-page screenshot sequence...")
            
            # Get page dimensions
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            print(f"📏 Page height: {page_height}px, Viewport: {viewport_height}px")
            
            screenshots = []
            current_position = 0
            screenshot_count = 0
            
            # Calculate overlap to ensure we don't miss content
            overlap = 100  # 100px overlap between screenshots
            scroll_step = viewport_height - overlap
            
            estimated_screenshots = max(1, int(page_height / scroll_step))
            print(f"📸 Estimated {estimated_screenshots} screenshots at full quality")
            
            while current_position < page_height:
                screenshot_count += 1
                print(f"📸 Taking screenshot {screenshot_count} at position {current_position}px")
                
                # Scroll to position
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                await asyncio.sleep(0.5)  # Wait for scroll to complete
                
                # Take screenshot of current viewport
                screenshot_bytes = await page.screenshot(
                    type="png",
                    full_page=False  # Only current viewport
                )
                
                # Preserve original quality (only resize if needed)
                optimized_screenshot = await self._optimize_screenshot_for_llm(screenshot_bytes)
                screenshots.append(optimized_screenshot)
                
                # Move to next position
                current_position += scroll_step
                
                # Safety check to prevent infinite loops
                if screenshot_count >= 10:  # Max 10 screenshots
                    print("⚠️ Max screenshots reached, stopping")
                    break
            
            total_size_mb = len(screenshots) * 250 / 1024  # Estimate ~250KB per screenshot
            print(f"✅ Captured {len(screenshots)} screenshots (~{total_size_mb:.1f}MB total)")
            return screenshots
            
        except Exception as e:
            print(f"⚠️ Full-page screenshot error: {e}")
            # Fallback to single screenshot
            screenshot_bytes = await page.screenshot(type="png", full_page=False)
            return [await self._optimize_screenshot_for_llm(screenshot_bytes)]

    async def _take_optimized_screenshot(self, page: Page) -> str:
        """Take optimized hero section screenshot"""
        try:
            screenshot_bytes = await page.screenshot(
                type="png",
                full_page=False  # Just viewport/hero section
            )
            
            return await self._optimize_screenshot_for_llm(screenshot_bytes)
            
        except Exception as e:
            print(f"⚠️ Screenshot error: {e}")
            return ""

    async def _generate_page_pdf(self, page: Page) -> str:
        """Generate PDF of the entire page"""
        try:
            pdf_bytes = await page.pdf(
                format='A4',
                print_background=True,        # Include background colors/images
                margin={
                    'top': '0.4in',
                    'right': '0.4in', 
                    'bottom': '0.4in',
                    'left': '0.4in'
                },
                prefer_css_page_size=False,   # Use our format
                scale=0.75                    # Fit more content
            )
            
            pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
            print(f"📄 PDF generated: {len(pdf_bytes)//1024}KB ({pdf_size_mb:.1f}MB)")
            
            # Check size limits (Claude API has limits)
            if pdf_size_mb > 32:  # Conservative limit
                print(f"⚠️ PDF large ({pdf_size_mb:.1f}MB), may hit API limits")
                
            return base64.b64encode(pdf_bytes).decode()
            
        except Exception as e:
            print(f"⚠️ PDF generation error: {e}")
            return ""

    async def _optimize_screenshot_for_llm(self, screenshot_bytes: bytes, max_dimension: int = 2048) -> str:
        """Preserve original screenshot quality, only resize if too large"""
        try:
            image = Image.open(io.BytesIO(screenshot_bytes))
            original_width, original_height = image.size
            original_size_kb = len(screenshot_bytes) // 1024
            
            print(f"📸 Original: {original_width}x{original_height} ({original_size_kb}KB)")
            
            # Only resize if really necessary (Claude's limits)
            if original_width > max_dimension or original_height > max_dimension:
                ratio = min(max_dimension / original_width, max_dimension / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                print(f"🔄 Resizing to: {new_width}x{new_height}")
                
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Keep as PNG for quality preservation
                buffer = io.BytesIO()
                resized_image.save(buffer, format="PNG", optimize=True)
                screenshot_bytes = buffer.getvalue()
                
                final_size_kb = len(screenshot_bytes) // 1024
                print(f"✅ Resized: {new_width}x{new_height} ({final_size_kb}KB)")
            else:
                print(f"✅ Size OK, preserving original quality: {original_size_kb}KB")
            
            return base64.b64encode(screenshot_bytes).decode()
            
        except Exception as e:
            print(f"⚠️ Screenshot optimization error: {e}")
            return base64.b64encode(screenshot_bytes).decode()

    async def _extract_dom_structure(self, page: Page) -> Dict[str, Any]:
        """Extract simplified DOM structure"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove scripts, styles, and comments
        for element in soup(["script", "style"]):
            element.decompose()
        
        for element in soup.find_all(string=lambda text: isinstance(text, Comment)):
            element.extract()
        
        # Extract structure
        structure = self._parse_element(soup.find('body') or soup)
        
        return {
            "structure": structure,
            "text_content": soup.get_text(separator=' ', strip=True)[:5000],
            "links": [{"text": a.get_text(strip=True), "href": a.get('href')} 
                     for a in soup.find_all('a', href=True)][:20],
            "images": [{"alt": img.get('alt', ''), "src": img.get('src')} 
                      for img in soup.find_all('img', src=True)][:10]
        }

    def _parse_element(self, element, max_depth=3, current_depth=0):
        """Parse DOM element into simplified structure"""
        if current_depth >= max_depth:
            return None
            
        if element.name is None:  # Text node
            text = element.strip()
            return {"type": "text", "content": text} if text else None
        
        result = {
            "tag": element.name,
            "attributes": {k: v for k, v in element.attrs.items() 
                          if k in ['class', 'id', 'href', 'src', 'alt']},
            "children": []
        }
        
        for child in element.children:
            parsed_child = self._parse_element(child, max_depth, current_depth + 1)
            if parsed_child:
                result["children"].append(parsed_child)
                
        return result

    async def _extract_styles(self, page: Page) -> Dict[str, Any]:
        """Extract computed styles for key elements"""
        styles_script = """
        () => {
            const styles = {};
            const elements = document.querySelectorAll('body, header, nav, main, footer, h1, h2, h3, p, a, button, .container, #main');
            
            elements.forEach((el, index) => {
                const computed = window.getComputedStyle(el);
                const selector = el.tagName.toLowerCase() + 
                    (el.id ? '#' + el.id : '') + 
                    (el.className ? '.' + el.className.split(' ').join('.') : '');
                
                styles[selector] = {
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    fontSize: computed.fontSize,
                    fontFamily: computed.fontFamily,
                    fontWeight: computed.fontWeight,
                    margin: computed.margin,
                    padding: computed.padding,
                    border: computed.border,
                    borderRadius: computed.borderRadius,
                    display: computed.display,
                    position: computed.position,
                    width: computed.width,
                    height: computed.height
                };
            });
            
            return styles;
        }
        """
        
        return await page.evaluate(styles_script)

    async def _extract_color_palette(self, page: Page) -> List[str]:
        """Extract dominant colors from the page"""
        try:
            screenshot_bytes = await page.screenshot(type="png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Extract dominant colors
            color_thief = colorthief.ColorThief(io.BytesIO(screenshot_bytes))
            palette = color_thief.get_palette(color_count=8, quality=1)
            
            # Convert to hex
            hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
            
            return hex_colors
        except Exception:
            return []

    async def _extract_fonts(self, page: Page) -> List[str]:
        """Extract font families used on the page"""
        fonts_script = """
        () => {
            const fonts = new Set();
            const elements = document.querySelectorAll('*');
            
            elements.forEach(el => {
                const style = window.getComputedStyle(el);
                const fontFamily = style.fontFamily;
                if (fontFamily) {
                    fonts.add(fontFamily);
                }
            });
            
            return Array.from(fonts).slice(0, 10);
        }
        """
        
        return await page.evaluate(fonts_script)

    async def _extract_layout_info(self, page: Page) -> Dict[str, Any]:
        """Extract layout and positioning information"""
        layout_script = """
        () => {
            const layout = {
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                body: {},
                sections: []
            };
            
            const body = document.body;
            if (body) {
                const rect = body.getBoundingClientRect();
                layout.body = {
                    width: rect.width,
                    height: rect.height,
                    scrollHeight: body.scrollHeight
                };
            }
            
            // Get main sections
            const sections = document.querySelectorAll('header, nav, main, section, footer, .container, .wrapper');
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                const computed = window.getComputedStyle(section);
                
                layout.sections.push({
                    tag: section.tagName.toLowerCase(),
                    className: section.className,
                    id: section.id,
                    dimensions: {
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left
                    },
                    styles: {
                        display: computed.display,
                        position: computed.position,
                        flexDirection: computed.flexDirection,
                        gridTemplateColumns: computed.gridTemplateColumns
                    }
                });
            });
            
            return layout;
        }
        """
        
        return await page.evaluate(layout_script)

    async def _extract_meta_data(self, page: Page) -> Dict[str, Any]:
        """Extract meta information and head tags"""
        meta_script = """
        () => {
            const meta = {
                title: document.title,
                description: '',
                keywords: '',
                og: {},
                twitter: {},
                links: []
            };
            
            // Meta tags
            const metaTags = document.querySelectorAll('meta');
            metaTags.forEach(tag => {
                const name = tag.getAttribute('name') || tag.getAttribute('property');
                const content = tag.getAttribute('content');
                
                if (name === 'description') meta.description = content;
                if (name === 'keywords') meta.keywords = content;
                if (name && name.startsWith('og:')) meta.og[name.replace('og:', '')] = content;
                if (name && name.startsWith('twitter:')) meta.twitter[name.replace('twitter:', '')] = content;
            });
            
            // Link tags (for stylesheets, icons, etc.)
            const linkTags = document.querySelectorAll('link');
            linkTags.forEach(link => {
                meta.links.push({
                    rel: link.rel,
                    href: link.href,
                    type: link.type
                });
            });
            
            return meta;
        }
        """
        
        return await page.evaluate(meta_script)