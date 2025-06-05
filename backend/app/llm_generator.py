# backend/app/services/llm_generator.py
import asyncio
import json
from typing import Dict, Any, Optional
import anthropic
import os
import base64
from io import BytesIO

class LLMGenerator:
    def __init__(self, provider: str = "anthropic", api_key: str = None):
        self.provider = provider
        self.api_key = api_key
        
        if provider == "anthropic":
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_html_clone(self, scraped_data: Dict[str, Any]) -> str:
        """Generate HTML clone from scraped data using multi-step approach"""
        
        print(f"🤖 Starting LLM generation for: {scraped_data.get('url')}")
        
        # Step 1: Analyze the design
        print("📊 Step 1: Analyzing design...")
        analysis = await self._analyze_design(scraped_data)
        
        # Step 2: Create structure plan
        print("🏗️ Step 2: Creating structure plan...")
        structure_plan = await self._create_structure_plan(scraped_data, analysis)
        
        # Step 3: Generate HTML
        print("🎨 Step 3: Generating HTML...")
        html_code = await self._generate_html(scraped_data, analysis, structure_plan)
        
        # Step 4: Refine and validate
        print("✨ Step 4: Refining HTML...")
        refined_html = await self._refine_html(html_code, scraped_data)
        
        print("✅ LLM generation completed!")
        return self._extract_html_code(refined_html)

    async def _analyze_design(self, scraped_data: Dict[str, Any]) -> str:
        """Step 1: Analyze the design and identify key components"""
        
        system_prompt = """You are an expert web designer analyzing a website's design. 
        Examine the provided data and identify:
        1. Overall layout pattern (header, nav, main, footer, sidebar)
        2. Color scheme and typography hierarchy
        3. Key visual components and their styling
        4. Navigation structure and user interface patterns
        5. Content organization and spacing patterns
        
        Be specific and detailed in your analysis. Focus on visual design elements that need to be recreated."""
        
        # Prepare the data for analysis
        analysis_data = {
            "title": scraped_data.get("title", ""),
            "dom_structure": scraped_data.get("dom_structure", {}),
            "color_palette": scraped_data.get("color_palette", []),
            "fonts": scraped_data.get("fonts", []),
            "layout_info": scraped_data.get("layout_info", {}),
            "styles": scraped_data.get("styles", {}),
            "meta_data": scraped_data.get("meta_data", {})
        }
        
        user_message = f"""
        Analyze this website design data:
        
        **Website Title:** {analysis_data['title']}
        
        **Color Palette:** {', '.join(analysis_data['color_palette'][:8]) if analysis_data['color_palette'] else 'No colors extracted'}
        
        **Typography:** {', '.join(analysis_data['fonts'][:5]) if analysis_data['fonts'] else 'No fonts extracted'}
        
        **Page Structure Info:**
        {json.dumps(analysis_data['layout_info'], indent=2)[:1500] if analysis_data['layout_info'] else 'No layout info'}
        
        **Content Preview:**
        {analysis_data['dom_structure'].get('text_content', '')[:1000] if analysis_data['dom_structure'] else 'No content'}
        
        **Navigation & Links:**
        {json.dumps(analysis_data['dom_structure'].get('links', [])[:10], indent=2) if analysis_data['dom_structure'] else 'No links found'}
        
        Provide a comprehensive design analysis focusing on visual elements, layout patterns, and styling approaches.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error in design analysis: {e}")
            return f"Basic analysis: {scraped_data.get('title', 'Website')} with {len(scraped_data.get('color_palette', []))} colors detected."

    async def _create_structure_plan(self, scraped_data: Dict[str, Any], analysis: str) -> str:
        """Step 2: Create a detailed HTML structure plan"""
        
        system_prompt = """Based on the design analysis, create a detailed HTML structure plan.
        Define:
        1. Semantic HTML structure (header, nav, main, sections, footer)
        2. CSS layout approach (flexbox, grid, positioning)
        3. Component breakdown and hierarchy
        4. Responsive design considerations
        5. Specific class names and styling strategy
        
        Be very specific about HTML tags, CSS classes, and layout techniques."""
        
        user_message = f"""
        Based on this design analysis:
        
        {analysis}
        
        And this DOM structure data:
        {json.dumps(scraped_data.get('dom_structure', {}), indent=2)[:2000]}
        
        Create a detailed HTML structure plan that will recreate this design. Include:
        - Exact HTML semantic structure
        - CSS class naming strategy  
        - Layout approach (flexbox/grid/positioning)
        - Component organization
        - Responsive considerations
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error in structure planning: {e}")
            return "Basic structure: Header, main content area, footer with responsive design."

    async def _generate_html(self, scraped_data: Dict[str, Any], analysis: str, structure_plan: str) -> str:
        """Step 3: Generate the actual HTML code"""
        
        system_prompt = """You are an expert frontend developer creating pixel-perfect HTML recreations.
        
        Generate a complete, self-contained HTML file that recreates the original website design.
        
        REQUIREMENTS:
        1. Use modern HTML5 semantic tags
        2. Include ALL CSS embedded in <style> tags (no external stylesheets)
        3. Make it fully responsive (mobile-first approach)
        4. Match colors, fonts, and layout as closely as possible
        5. Include realistic placeholder content that matches the original structure
        6. Use modern CSS (Flexbox, Grid, CSS Variables)
        7. Ensure visual similarity to the original design
        8. Include hover effects and basic interactions where appropriate
        
        Return ONLY the complete HTML code, no explanations or markdown."""
        
        # Prepare rich context for generation
        colors_list = scraped_data.get('color_palette', [])[:8]
        fonts_list = scraped_data.get('fonts', [])[:5]
        content_preview = scraped_data.get('dom_structure', {}).get('text_content', '')[:800]
        
        user_message = f"""
        Create complete HTML that recreates this website:
        
        **DESIGN ANALYSIS:**
        {analysis}
        
        **STRUCTURE PLAN:**
        {structure_plan}
        
        **DESIGN DATA:**
        - Title: {scraped_data.get('title', 'Website')}
        - Primary Colors: {', '.join(colors_list) if colors_list else 'Use modern neutral palette'}
        - Typography: {', '.join(fonts_list) if fonts_list else 'Use modern system fonts'}
        - Original URL: {scraped_data.get('url', '')}
        
        **CONTENT CONTEXT:**
        {content_preview}
        
        **LAYOUT INFO:**
        Viewport: {scraped_data.get('layout_info', {}).get('viewport', {})}
        
        Generate a complete, modern HTML page that visually recreates this design. Focus on:
        - Exact color matching
        - Typography hierarchy
        - Layout structure and spacing
        - Professional, polished appearance
        - Mobile responsiveness
        """
        
        # Add screenshot context if available
        messages = [{"role": "user", "content": user_message}]
        
        # Include screenshot for visual context
        if scraped_data.get("screenshot_base64"):
            try:
                messages[0]["content"] = [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": scraped_data["screenshot_base64"]
                        }
                    }
                ]
                print("📷 Including screenshot for visual analysis")
            except Exception as e:
                print(f"⚠️ Could not include screenshot: {e}")
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error in HTML generation: {e}")
            return self._create_fallback_html(scraped_data)

    async def _refine_html(self, html_code: str, scraped_data: Dict[str, Any]) -> str:
        """Step 4: Refine and validate the generated HTML"""
        
        system_prompt = """Review and refine the HTML code to ensure:
        1. Valid HTML5 structure with proper DOCTYPE
        2. No missing closing tags or syntax errors
        3. Clean, well-formatted CSS
        4. Proper responsive design implementation
        5. Accessibility considerations (alt tags, semantic structure)
        6. Performance optimizations
        7. Cross-browser compatibility
        
        Return only the refined, production-ready HTML code."""
        
        colors = scraped_data.get('color_palette', [])[:5]
        fonts = scraped_data.get('fonts', [])[:3]
        
        user_message = f"""
        Refine and optimize this HTML code:
        
        ```html
        {html_code[:3000]}{"..." if len(html_code) > 3000 else ""}
        ```
        
        DESIGN CONTEXT:
        - Colors to preserve: {', '.join(colors) if colors else 'Modern palette'}
        - Fonts to use: {', '.join(fonts) if fonts else 'System fonts'}
        - Original title: {scraped_data.get('title', 'Website')}
        
        Ensure the code is:
        - Syntactically perfect
        - Responsive and accessible
        - Visually polished
        - Performance optimized
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error in HTML refinement: {e}")
            return html_code  # Return original if refinement fails

    def _extract_html_code(self, response: str) -> str:
        """Extract clean HTML code from LLM response"""
        # Remove markdown code blocks if present
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
        
        # Ensure proper DOCTYPE if missing
        if not html.strip().startswith(('<!DOCTYPE', '<html')):
            html = f"<!DOCTYPE html>\n{html}"
        
        return html

    def _create_fallback_html(self, scraped_data: Dict[str, Any]) -> str:
        """Create fallback HTML when LLM fails"""
        
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
        .fallback {{ 
            background: #f8f9fa; padding: 2rem; margin: 2rem 0; 
            border-left: 4px solid {colors[2] if len(colors) > 2 else '#007bff'}; 
        }}
    </style>
</head>
<body>
    <header><h1>{title}</h1></header>
    <main class="container">
        <div class="fallback">
            <h2>LLM Generation Fallback</h2>
            <p>The AI service encountered an issue. This is a basic fallback layout.</p>
        </div>
    </main>
</body>
</html>"""