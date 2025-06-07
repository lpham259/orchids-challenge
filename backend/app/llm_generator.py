import asyncio
from typing import Dict, Any, Optional, List
import anthropic
import base64
from PIL import Image
import io

class LLMGenerator:
    def __init__(self, provider: str = "anthropic", api_key: str = None):
        self.provider = provider
        self.api_key = api_key
        
        if provider == "anthropic":
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_html_clone(self, scraped_data: Dict[str, Any]) -> str:
        """Generate HTML clone using PDF-first approach"""
        
        print(f"🤖 Starting AI generation for: {scraped_data.get('url')}")
        
        # Get the best visual input (PDF priority)
        visual_data, input_type = self._get_best_visual_input(scraped_data)
        
        if visual_data:
            print(f"🎯 Using {input_type} input for AI analysis")
            html_code = await self._direct_visual_clone(visual_data, input_type, scraped_data)
        else:
            print("⚠️ No visual input available, using fallback")
            html_code = self._create_fallback_html(scraped_data)
        
        print("✅ AI generation completed!")
        return self._extract_html_code(html_code)

    def _get_best_visual_input(self, scraped_data: Dict[str, Any]) -> tuple[Optional[Any], str]:
        """Get the best visual input - Full page screenshots priority"""
        
        print("🔍 Looking for visual inputs...")
        
        # Priority 1: Full page screenshots (NEW)
        full_screenshots = scraped_data.get("full_page_screenshots")
        if full_screenshots and len(full_screenshots) > 0:
            print(f"📸 Found {len(full_screenshots)} full-page screenshots")
            return full_screenshots, "screenshots"
        
        # Priority 2: PDF (fallback)
        pdf_data = scraped_data.get("pdf_base64")
        if pdf_data:
            print(f"📄 Found PDF: {len(pdf_data)} characters")
            return pdf_data, "pdf"
        
        # Priority 3: Single screenshot (last resort)
        screenshot_candidates = [
            ("screenshot_base64", scraped_data.get("screenshot_base64")),
            ("screenshot_hero", scraped_data.get("screenshot_hero")),
        ]
        
        for name, screenshot in screenshot_candidates:
            if screenshot:
                print(f"📸 Found {name}: {len(screenshot)} characters")
                if self._validate_screenshot_size(screenshot):
                    print(f"✅ Using {name} (size validated)")
                    return [screenshot], "screenshots"
        
        print("❌ No valid visual inputs found!")
        return None, "none"

    def _validate_screenshot_size(self, screenshot_base64: str) -> bool:
        """Validate screenshot is within Claude's limits"""
        try:
            image_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
            
            # Claude's practical limits
            is_valid = width <= 3000 and height <= 3000
            print(f"📸 Size check: {width}x{height} = {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Size validation error: {e}")
            return False

    async def _direct_visual_clone(self, visual_data: str, input_type: str, scraped_data: Dict[str, Any]) -> str:
        """Generate HTML from visual input - Screenshots priority"""
    
        if input_type == "screenshots":
            print(f"📸 Processing screenshots...")
            if isinstance(visual_data, list) and len(visual_data) > 1:
                return await self._process_multiple_screenshots(visual_data, scraped_data)
            else:
                # Single screenshot
                screenshot = visual_data[0] if isinstance(visual_data, list) else visual_data
                return await self._process_image_input(screenshot, scraped_data)
        
        elif input_type == "pdf":
            # ... existing PDF logic ...
            print("📄 Processing PDF with Claude's official API...")
            pdf_result = await self._process_pdf_input(visual_data, scraped_data)
            if pdf_result:
                return pdf_result
            
            # Fallback: Convert PDF to image
            print("📄 PDF API failed, converting to image...")
            image_data = await self._convert_pdf_to_image(visual_data)
            if image_data:
                print("📄 Successfully converted PDF to image")
                return await self._process_image_input(image_data, scraped_data)
            
            # Final fallback: Use screenshot
            print("📄 PDF conversion failed, using screenshot...")
            screenshot = scraped_data.get("screenshot_base64")
            if screenshot and self._validate_screenshot_size(screenshot):
                return await self._process_image_input(screenshot, scraped_data)
            
            return self._create_fallback_html(scraped_data)
        
        else:
            # Process image input (screenshot)
            print(f"📸 Processing image input...")
            return await self._process_image_input(visual_data, scraped_data)

    async def _process_pdf_input(self, pdf_data: str, scraped_data: Dict[str, Any]) -> Optional[str]:
        """Process PDF with emphasis on complete page recreation"""
        
        # Enhanced prompt that emphasizes the COMPLETE page recreation
        system_prompt = """You are an expert web developer. I'm providing you with a PDF that shows a complete multi-page website. 

This PDF contains ALL the content from the website - multiple pages/sections that represent the full scrollable webpage.

Your task: Create a single HTML page that includes ALL the content and sections shown across ALL pages of this PDF."""

        user_message = """This PDF shows a complete website across multiple pages. Please create ONE complete HTML file that includes ALL the content from ALL pages of this PDF. 

Make sure to recreate:
- Prioritize visual replication
- ALL sections shown across all PDF pages
- The complete scrollable webpage content
- All visual elements, colors, and layout from every page

Can you visually duplicate this COMPLETE multi-page PDF into one comprehensive HTML page?"""

        try:
            messages = [{
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_message},
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    }
                ]
            }]
            
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,  # Doubled for complete page content
                system=system_prompt,
                messages=messages
            )
            
            print("✅ PDF processed with complete page emphasis!")
            return response.content[0].text
            
        except Exception as e:
            print(f"❌ PDF processing error: {str(e)}")
            
            # Try the exact original prompt as backup
            print("🔄 Trying original simple prompt...")
            try:
                simple_messages = [{
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": "Can you visually duplicate this PDF into pure HTML? Include all pages."},
                        {
                            "type": "document",
                            "source": {
                                "type": "base64", 
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        }
                    ]
                }]
                
                simple_response = await self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    messages=simple_messages
                )
                
                print("✅ Simple prompt worked!")
                return simple_response.content[0].text
                
            except Exception as e2:
                print(f"❌ Simple prompt also failed: {str(e2)}")
                return None
    
    async def _process_multiple_screenshots(self, screenshots: List[str], scraped_data: Dict[str, Any]) -> str:
        """Process multiple screenshots to create complete webpage"""
        
        print(f"📸 Processing {len(screenshots)} screenshots for complete webpage")
        
        system_prompt = """You are an expert web developer. I'm providing you with multiple screenshots that show a complete webpage from top to bottom.

    These screenshots were taken by scrolling down the page, so they show the ENTIRE website content in sequence.

    Your task: Create ONE complete HTML page that includes ALL the content shown across ALL these screenshots in the correct order."""

        # Build the user message with all screenshots
        content = [
            {
                "type": "text", 
                "text": f"""I'm providing {len(screenshots)} sequential screenshots of a complete webpage taken from top to bottom.

    Please create ONE comprehensive HTML file that recreates ALL the content shown across these {len(screenshots)} screenshots in the correct order.

    Make sure to:
    - Prioritize visual replication
    - Include ALL sections from every screenshot
    - Maintain the correct top-to-bottom sequence
    - Recreate all visual elements, colors, and layouts
    - Create one seamless scrollable webpage

    Can you create a complete HTML page from these {len(screenshots)} sequential screenshots?"""
            }
        ]
        
        # Add all screenshots to the message
        for i, screenshot in enumerate(screenshots):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot
                }
            })

        try:
            messages = [{"role": "user", "content": content}]
            
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                system=system_prompt,
                messages=messages
            )
            
            print("✅ Multiple screenshots processed successfully!")
            return response.content[0].text
            
        except Exception as e:
            print(f"❌ Multiple screenshot processing error: {e}")
            # Fallback to first screenshot only
            return await self._process_image_input(screenshots[0], scraped_data)

    async def _process_image_input(self, image_data: str, scraped_data: Dict[str, Any]) -> str:
        """Process image input with the same direct approach"""
        
        # Keep it simple and direct like the manual approach
        system_prompt = """You are an expert web developer. Look at this image and create HTML that visually duplicates it."""

        user_message = "Can you visually duplicate this image into pure HTML?"

        try:
            messages = [{
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }]
            
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            return self._create_fallback_html(scraped_data)

    async def _convert_pdf_to_image(self, pdf_base64: str) -> Optional[str]:
        """Convert PDF to high-quality image for Claude"""
        try:
            print("📄 Converting PDF to image...")
            
            import fitz  # PyMuPDF
            
            # Decode PDF
            pdf_bytes = base64.b64decode(pdf_base64)
            
            # Open PDF with PyMuPDF
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Convert first page to high-resolution image
            page = pdf_doc[0]
            mat = fitz.Matrix(2.0, 2.0)  # 2x scaling for quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Optimize size for Claude (keep it reasonable)
            max_dimension = 2048
            if image.width > max_dimension or image.height > max_dimension:
                ratio = min(max_dimension / image.width, max_dimension / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert back to base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            print(f"✅ PDF converted to image: {image.width}x{image.height}")
            pdf_doc.close()
            return image_base64
            
        except ImportError:
            print("❌ PyMuPDF not installed - run: pip install PyMuPDF")
            return None
        except Exception as e:
            print(f"❌ PDF conversion failed: {e}")
            return None

    def _extract_html_code(self, response: str) -> str:
        """Extract clean HTML code from LLM response"""
        # Remove markdown code blocks
        if "```html" in response:
            start = response.find("```html") + 7
            end = response.find("```", start)
            if end != -1:
                html = response[start:end].strip()
            else:
                html = response[response.find("```html") + 7:].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                html = response[start:end].strip()
            else:
                html = response[response.find("```") + 3:].strip()
        else:
            html = response.strip()
        
        # Ensure proper DOCTYPE
        if not html.strip().startswith(('<!DOCTYPE', '<html')):
            html = f"<!DOCTYPE html>\n{html}"
        
        return html

    def _create_fallback_html(self, scraped_data: Dict[str, Any]) -> str:
        """Create fallback HTML when AI generation fails"""
        
        title = scraped_data.get('title', 'Cloned Website')
        colors = scraped_data.get('color_palette', ['#333333', '#ffffff', '#007bff'])[:3]
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {colors[1] if len(colors) > 1 else '#ffffff'};
            color: {colors[0] if colors else '#333333'};
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ 
            background: {colors[0] if colors else '#333333'}; 
            color: {colors[1] if len(colors) > 1 else '#ffffff'}; 
            padding: 2rem 0; text-align: center; 
        }}
        .notice {{ 
            background: #f8f9fa; padding: 2rem; margin: 2rem 0; 
            border-left: 4px solid {colors[2] if len(colors) > 2 else '#007bff'}; 
        }}
    </style>
</head>
<body>
    <header><h1>{title}</h1></header>
    <main class="container">
        <div class="notice">
            <h2>AI Website Clone</h2>
            <p>Fallback mode - check API configuration for full AI generation.</p>
        </div>
    </main>
</body>
</html>"""