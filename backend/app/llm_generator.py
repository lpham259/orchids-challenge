import asyncio
import json
from typing import Dict, Any, Optional
import anthropic
import os
import base64

class LLMGenerator:
    def __init__(self, provider: str = "anthropic", api_key: str = None, debug: bool = True):
        self.provider = provider
        self.api_key = api_key
        self.debug = debug  # Add debug flag
        
        if provider == "anthropic":
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _debug_print(self, message: str):
        """Print debug messages with clear formatting"""
        if self.debug:
            print(f"\n{'='*50}")
            print(f"🔧 LLM DEBUG: {message}")
            print(f"{'='*50}\n")

    async def generate_html_clone(self, scraped_data: Dict[str, Any]) -> str:
        """SIMPLIFIED: Direct visual recreation from screenshot"""
        
        self._debug_print(f"Starting generation for: {scraped_data.get('url')}")
        
        # Get the best available screenshot
        screenshot = self._get_best_screenshot(scraped_data)
        
        if screenshot:
            self._debug_print("✅ Screenshot found - using direct visual approach")
            html_code = await self._direct_visual_clone(screenshot, scraped_data)
        else:
            self._debug_print("❌ NO SCREENSHOT FOUND - using fallback")
            self._debug_print(f"Available keys: {list(scraped_data.keys())}")
            html_code = self._create_fallback_html(scraped_data)
        
        self._debug_print("Generation completed!")
        return self._extract_html_code(html_code)

    def _get_best_screenshot(self, scraped_data: Dict[str, Any]) -> Optional[str]:
        """Get the best screenshot for visual cloning"""
        
        # Priority order: hero > base64 > first section > mobile
        candidates = [
            ("screenshot_hero", scraped_data.get("screenshot_hero")),
            ("screenshot_base64", scraped_data.get("screenshot_base64")), 
            ("section_1", scraped_data.get("screenshot_sections", {}).get("section_1")),
            ("screenshot_mobile", scraped_data.get("screenshot_mobile"))
        ]
        
        self._debug_print("🔍 Looking for screenshots...")
        
        for name, screenshot in candidates:
            if screenshot:
                self._debug_print(f"Found {name}: {len(screenshot)} characters")
                if self._validate_screenshot_size(screenshot):
                    self._debug_print(f"✅ Using {name} (size validated)")
                    return screenshot
                else:
                    self._debug_print(f"❌ {name} too large (size validation failed)")
            else:
                self._debug_print(f"❌ {name} not found")
        
        self._debug_print("❌ No valid screenshots found!")
        return None

    def _validate_screenshot_size(self, screenshot_base64: str) -> bool:
        """Validate screenshot is within Claude's limits"""
        try:
            import base64
            from PIL import Image
            import io
            
            image_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
            
            print(f"🔍 DEBUG: Screenshot size: {width}x{height}")
            
            # Conservative limits for reliable processing
            is_valid = width <= 3000 and height <= 3000
            print(f"🔍 DEBUG: Size validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            return is_valid
            
        except Exception as e:
            print(f"❌ DEBUG: Validation error: {e}")
            return False

    async def _direct_visual_clone(self, screenshot_base64: str, scraped_data: Dict[str, Any]) -> str:
        """Ultra-direct visual cloning - exactly like manual approach"""
        
        # ULTRA-SIMPLE PROMPT (like your manual approach)
        system_prompt = """You are an expert web developer. Look at this image and create HTML that looks exactly like it.

Use modern HTML5 and CSS3 with embedded styles. Focus purely on visual recreation.

Return only the HTML code."""

        # MINIMAL PROMPT - Just like "give me pure html that will look like this:"
        user_message = "Give me pure HTML that will look exactly like this:"

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
                            "data": screenshot_base64
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
            print(f"Error in direct visual cloning: {e}")
            return self._create_fallback_html(scraped_data)

    def _extract_html_code(self, response: str) -> str:
        """Extract HTML from response"""
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
        
        if not html.strip().startswith(('<!DOCTYPE', '<html')):
            html = f"<!DOCTYPE html>\n{html}"
        
        return html

    def _create_fallback_html(self, scraped_data: Dict[str, Any]) -> str:
        """Fallback when no screenshot available"""
        
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
            <h2>Direct Visual Clone</h2>
            <p>Simplified approach for better visual accuracy.</p>
        </div>
    </main>
</body>
</html>"""