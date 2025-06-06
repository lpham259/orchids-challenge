import asyncio
import base64
import json
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page
from urllib.parse import urljoin, urlparse
import colorthief
from PIL import Image
import io
import re
from bs4 import BeautifulSoup, Comment

class WebsiteScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """SIMPLIFIED: Focus on getting one good screenshot + basic data"""
        page = await self.browser.new_page()
        
        try:
            # Navigate to the page
            await page.goto(str(url), wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Let dynamic content load
            
            # Set optimal viewport for desktop
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
            # Take ONE high-quality hero screenshot
            print("📸 Capturing hero section...")
            screenshot_base64 = await self._take_optimized_screenshot(page)
            
            # Extract other data
            scraped_data = {
                "url": str(url),
                "title": await page.title(),
                "screenshot_base64": screenshot_base64,  # Main screenshot
                "screenshot_hero": screenshot_base64,    # For compatibility
                "dom_structure": await self._extract_dom_structure(page),
                "styles": await self._extract_styles(page),
                "color_palette": await self._extract_color_palette(page),
                "fonts": await self._extract_fonts(page),
                "layout_info": await self._extract_layout_info(page),
                "meta_data": await self._extract_meta_data(page)
            }
            
            print(f"✅ Screenshot captured: {'Yes' if screenshot_base64 else 'Failed'}")
            return scraped_data
            
        except Exception as e:
            raise Exception(f"Failed to scrape website: {str(e)}")
        finally:
            await page.close()

    async def _take_optimized_screenshot(self, page: Page) -> str:
        """Take one optimized screenshot for LLM analysis"""
        try:
            # Take hero section screenshot (no quality parameter for PNG)
            screenshot_bytes = await page.screenshot(
                type="png",
                full_page=False  # Just viewport, not full page
            )
            
            # Optimize for Claude's limits
            return await self._optimize_screenshot_for_llm(screenshot_bytes)
            
        except Exception as e:
            print(f"⚠️ Screenshot error: {e}")
            return ""

    async def _optimize_screenshot_for_llm(self, screenshot_bytes: bytes, max_dimension: int = 2048) -> str:
        """Optimize screenshot size for LLM processing"""
        try:
            from PIL import Image
            import io
            
            # Open image
            image = Image.open(io.BytesIO(screenshot_bytes))
            original_width, original_height = image.size
            
            print(f"📸 Original: {original_width}x{original_height}")
            
            # Resize if too large
            if original_width > max_dimension or original_height > max_dimension:
                ratio = min(max_dimension / original_width, max_dimension / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                print(f"🔄 Resizing to: {new_width}x{new_height}")
                
                # High-quality resize
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert back to bytes
                buffer = io.BytesIO()
                resized_image.save(buffer, format="PNG", optimize=True)
                screenshot_bytes = buffer.getvalue()
                
                print(f"✅ Optimized size: {len(screenshot_bytes)//1024}KB")
            else:
                print(f"✅ Size OK: {len(screenshot_bytes)//1024}KB")
            
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
            # Take screenshot for color analysis (no quality param)
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