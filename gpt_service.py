import os
import time
import base64
from openai import OpenAI
from typing import Tuple, Dict, Optional

class GPTService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.last_request_time = 0
        self.min_request_interval = 1
    
    def _get_settings(self):
        """Load brand settings from database"""
        try:
            from app import app, db
            from models import Settings
            
            with app.app_context():
                settings = Settings.query.first()
                
                if not settings:
                    return {
                        'company_name': 'Prompt Creative',
                        'branded_hashtag': '#ShopPromptCreative',
                        'shop_url': '',
                        'instagram_hashtag_count': 8,
                        'pinterest_hashtag_count': 4,
                        'content_tone': 'balanced'
                    }
                
                return {
                    'company_name': settings.company_name or 'Prompt Creative',
                    'branded_hashtag': settings.branded_hashtag or '#ShopPromptCreative',
                    'shop_url': settings.shop_url or '',
                    'instagram_hashtag_count': settings.instagram_hashtag_count or 8,
                    'pinterest_hashtag_count': settings.pinterest_hashtag_count or 4,
                    'content_tone': settings.content_tone or 'balanced'
                }
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {
                'company_name': 'Prompt Creative',
                'branded_hashtag': '#ShopPromptCreative',
                'shop_url': '',
                'instagram_hashtag_count': 8,
                'pinterest_hashtag_count': 4,
                'content_tone': 'balanced'
            }
    
    def _get_tone_guidance(self, tone: str) -> str:
        """Get tone-specific guidance for content generation"""
        tone_templates = {
            'poetic': """
TONE: Artistic and poetic. Use evocative, flowing language that captures the emotional essence.
Example: "Dance in the lively moonlight of this vibrant acrylic creation..."
Style: Emphasize mood, feeling, artistic expression""",
            
            'balanced': """
TONE: Balanced mix of artistry and approachability. Describe the artwork while keeping it relatable.
Example: "This vibrant acrylic piece captures movement and energy, perfect for brightening any space..."
Style: Blend aesthetic appreciation with practical appeal""",
            
            'direct': """
TONE: Direct and sales-focused. Clear, concise descriptions that highlight value.
Example: "Original acrylic art. Bold colors, professional quality. Shop now at [shop link]"
Style: Emphasize uniqueness, value, call-to-action"""
        }
        
        return tone_templates.get(tone, tone_templates['balanced'])

    def _rate_limit(self):
        """Simple rate limiting implementation"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def analyze_image_and_generate_content(
        self,
        image_path: str,
        painting_name: str,
        platform: str = "all",
        materials: Optional[str] = None,
        size: Optional[str] = None,
        artist_note: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Analyze artwork image using GPT-4 Vision and generate platform-specific content
        
        Args:
            image_path: Path to the image file
            painting_name: Name of the painting
            platform: Target platform (instagram, pinterest, etsy, or all)
            materials: Materials used (e.g., "Acrylic Mixed Media, Acrylic pour")
            size: Artwork dimensions (e.g., "18x24x1")
            artist_note: Personal story or context about the artwork
        
        Returns:
            Dictionary with platform-specific content fields
        """
        self._rate_limit()
        
        settings = self._get_settings()
        company_name = settings['company_name']
        tone_guidance = self._get_tone_guidance(settings['content_tone'])
        ig_hashtag_count = settings['instagram_hashtag_count']
        pinterest_hashtag_count = settings['pinterest_hashtag_count']
        branded_hashtag = settings['branded_hashtag']
        
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error reading image: {e}")
            return self._generate_fallback_content(painting_name, platform)
        
        platform_prompts = {
            "instagram": f"""Analyze this artwork and create Instagram content for {company_name}:

{tone_guidance}

1. A captivating caption (2-3 sentences, front-load best content in first 125 characters for feed preview)
2. Instagram first comment with relevant hashtags ({ig_hashtag_count} hashtags - quality over quantity, including art style, colors, medium, mood)
3. SEO-friendly title (MAX 90 characters)
4. SEO description
5. SEO tags (comma-separated keywords)

IMPORTANT: 
- First 125 characters of caption appear in feed before "...more" - make them count!
- Generate EXACTLY {ig_hashtag_count} high-quality hashtags
- Content created by {company_name}

Format your response as:
CAPTION: [caption text - best content in first 125 chars]
FIRST_COMMENT: [{ig_hashtag_count} hashtags only - do NOT include {branded_hashtag} as it will be added automatically]
SEO_TITLE: [title - MAX 90 chars]
SEO_DESCRIPTION: [description]
SEO_TAGS: [tags]""",
            
            "pinterest": f"""Analyze this artwork and create Pinterest content for {company_name}:

{tone_guidance}

1. Pinterest description (MAXIMUM 450 characters including spaces - this is a HARD LIMIT, keyword-rich for search)
2. Pinterest board category suggestion (MAXIMUM 90 characters)
3. Hashtags ({pinterest_hashtag_count} relevant hashtags for Pinterest discovery)
4. Link URL suggestion (where to link this pin)
5. SEO title (MAXIMUM 90 characters)
6. SEO description
7. SEO tags (comma-separated keywords)
8. Alt text for accessibility

CRITICAL: Pinterest has strict character limits. Posts will FAIL if exceeded.
- Description MUST be under 450 characters
- Title/Board names MUST be under 90 characters
- Generate EXACTLY {pinterest_hashtag_count} hashtags
- Content created by {company_name}

Format your response as:
PINTEREST_DESC: [description - MAX 450 chars]
PINTEREST_BOARD: [board name - MAX 90 chars]
PINTEREST_HASHTAGS: [{pinterest_hashtag_count} hashtags for Pinterest - do NOT include {branded_hashtag} as it will be added automatically]
PINTEREST_LINK: [suggested link]
SEO_TITLE: [title - MAX 90 chars]
SEO_DESCRIPTION: [description]
SEO_TAGS: [tags]
ALT_TEXT: [accessibility description]""",
            
            "etsy": f"""Analyze this artwork and create Etsy listing content for {company_name}:

{tone_guidance}

1. Listing title (engaging, keyword-rich, under 140 chars)
2. Full description (detailed, 2-3 paragraphs about the artwork, style, colors, mood, what makes it special)
3. SEO tags (13 relevant keywords/phrases for Etsy search)
4. Suggested price range
5. Alt text for accessibility

IMPORTANT:
- Content created by {company_name}
- Emphasize original artwork and professional quality

Format your response as:
ETSY_TITLE: [title]
ETSY_DESC: [full description]
SEO_TAGS: [13 tags separated by commas]
ETSY_PRICE: [suggested price range like "$25-50"]
ALT_TEXT: [accessibility description]""",
            
            "all": """Analyze this artwork and create comprehensive content for ALL platforms (Instagram, Pinterest, Etsy):

INSTAGRAM:
- Caption (2-3 sentences, first 125 characters are most important for preview)
- First comment hashtags (15-25 hashtags maximum - quality over quantity)

PINTEREST:
- Description (keyword-rich, MAXIMUM 450 characters - HARD LIMIT)
- Board category (MAXIMUM 90 characters)
- Hashtags (15-20 hashtags optimized for Pinterest discovery)
- Link suggestion

ETSY:
- Listing title (engaging, under 140 chars)
- Full description (2-3 paragraphs)
- Price range suggestion

GENERAL:
- SEO title (MAXIMUM 90 characters for consistency)
- SEO description
- SEO tags (comprehensive list)
- Alt text for accessibility
- General text/caption

CRITICAL CHARACTER LIMITS (posts will FAIL if exceeded):
- Pinterest description: MAX 450 characters
- Pinterest board/title: MAX 90 characters
- Instagram: First 125 chars show in feed preview
- Hashtags: 15-25 is optimal (avoid spam)

Format your response as:
IG_CAPTION: [caption - front-load best content in first 125 chars]
IG_FIRST_COMMENT: [15-25 hashtags for Instagram]
PINTEREST_DESC: [description - MAX 450 chars]
PINTEREST_BOARD: [board - MAX 90 chars]
PINTEREST_HASHTAGS: [15-20 hashtags for Pinterest]
PINTEREST_LINK: [link]
ETSY_TITLE: [title - under 140 chars]
ETSY_DESC: [description]
ETSY_PRICE: [price]
SEO_TITLE: [title - MAX 90 chars]
SEO_DESCRIPTION: [description]
SEO_TAGS: [tags]
ALT_TEXT: [alt text]
TEXT: [general caption]"""
        }
        
        prompt = platform_prompts.get(platform.lower(), platform_prompts["all"])
        
        artwork_details = f"Painting name: '{painting_name}'"
        if materials:
            artwork_details += f"\nMaterials: {materials}"
        if size:
            artwork_details += f"\nSize: {size}"
        if artist_note:
            artwork_details += f"\nArtist's Note: {artist_note}"
        
        prompt = f"{artwork_details}\n\n{prompt}\n\nIMPORTANT: \n1. Describe the COLORS you see in the artwork (specific shades like 'deep turquoise', 'warm coral', 'soft lavender')\n2. Incorporate the size, materials, and artist's personal note into your descriptions\n3. Make the content unique, vivid, and authentic by focusing on visual details"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert art curator and digital marketing specialist. Analyze artwork images carefully, describing specific COLORS, textures, and visual elements you observe. Create compelling, SEO-optimized content for social media and e-commerce platforms that helps viewers visualize the artwork."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content or ""
            return self._parse_platform_response(content, platform)
            
        except Exception as e:
            print(f"Error with vision API: {e}")
            return self._generate_fallback_content(painting_name, platform)

    def _parse_platform_response(self, content: str, platform: str) -> Dict[str, str]:
        """Parse the GPT response into structured fields"""
        result = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                field_mapping = {
                    'CAPTION': 'text',
                    'IG_CAPTION': 'text',
                    'FIRST_COMMENT': 'instagram_first_comment',
                    'IG_FIRST_COMMENT': 'instagram_first_comment',
                    'PINTEREST_HASHTAGS': 'pinterest_hashtags',
                    'PINTEREST_DESC': 'pinterest_description',
                    'PINTEREST_BOARD': 'pin_board_fb_album_google_category',
                    'PINTEREST_LINK': 'pinterest_link_url',
                    'ETSY_TITLE': 'etsy_listing_title',
                    'ETSY_DESC': 'etsy_description',
                    'ETSY_PRICE': 'etsy_price',
                    'SEO_TITLE': 'seo_title',
                    'SEO_DESCRIPTION': 'seo_description',
                    'SEO_TAGS': 'seo_tags',
                    'ALT_TEXT': 'alt_text',
                    'TEXT': 'text'
                }
                
                if key in field_mapping:
                    result[field_mapping[key]] = value
        
        result = self._enforce_character_limits(result)
        result = self._append_branded_hashtag(result)
        return result
    
    def _append_branded_hashtag(self, content: Dict[str, str]) -> Dict[str, str]:
        """Append branded hashtag to Instagram and Pinterest hashtags"""
        try:
            settings = self._get_settings()
            branded_hashtag = settings['branded_hashtag']
            
            if not branded_hashtag:
                return content
            
            if 'instagram_first_comment' in content and content['instagram_first_comment']:
                if branded_hashtag not in content['instagram_first_comment']:
                    content['instagram_first_comment'] += f" {branded_hashtag}"
            
            if 'pinterest_hashtags' in content and content['pinterest_hashtags']:
                if branded_hashtag not in content['pinterest_hashtags']:
                    content['pinterest_hashtags'] += f" {branded_hashtag}"
            
            return content
        except Exception as e:
            print(f"Error appending branded hashtag: {e}")
            return content
    
    def _enforce_character_limits(self, content: Dict[str, str]) -> Dict[str, str]:
        """Enforce strict character limits on generated content"""
        if 'pinterest_description' in content and content['pinterest_description']:
            if len(content['pinterest_description']) > 450:
                content['pinterest_description'] = content['pinterest_description'][:447] + '...'
        
        if 'pin_board_fb_album_google_category' in content and content['pin_board_fb_album_google_category']:
            if len(content['pin_board_fb_album_google_category']) > 90:
                content['pin_board_fb_album_google_category'] = content['pin_board_fb_album_google_category'][:87] + '...'
        
        if 'seo_title' in content and content['seo_title']:
            if len(content['seo_title']) > 90:
                content['seo_title'] = content['seo_title'][:87] + '...'
        
        if 'video_pin_pdf_title' in content and content['video_pin_pdf_title']:
            if len(content['video_pin_pdf_title']) > 90:
                content['video_pin_pdf_title'] = content['video_pin_pdf_title'][:87] + '...'
        
        return content

    def _generate_fallback_content(self, painting_name: str, platform: str) -> Dict[str, str]:
        """Generate basic content when vision API fails"""
        return {
            'text': f"Beautiful artwork: {painting_name}",
            'seo_tags': f"art, painting, {painting_name.lower()}",
            'seo_title': painting_name,
            'seo_description': f"Original artwork titled {painting_name}",
            'alt_text': f"Artwork titled {painting_name}"
        }

    def generate_artwork_content(
        self, 
        category: str, 
        filename: str, 
        feedback: Optional[str] = None
    ) -> Tuple[str, str]:
        """Legacy method for backward compatibility"""
        self._rate_limit()

        base_prompt = (
            f"Generate a creative and engaging description and relevant hashtags for an artwork.\n"
            f"Category/Title: {category}\n"
            f"Filename: {filename}\n"
        )

        if feedback:
            base_prompt += f"Previous feedback: {feedback}\n"

        base_prompt += (
            "\nProvide the response in the following format:\n"
            "Description: [engaging description of the artwork]\n"
            "Hashtags: [relevant hashtags starting with #]"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an art curator helping to describe and categorize artwork."},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            content = response.choices[0].message.content
            description, hashtags = self._parse_response(content)
            
            return description, hashtags

        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return (
                f"Description for {filename}",
                f"#art #{category.lower().replace(' ', '')}"
            )

    def _parse_response(self, content: str) -> Tuple[str, str]:
        """Parse GPT response into description and hashtags"""
        try:
            lines = content.split('\n')
            description = ""
            hashtags = ""
            
            for line in lines:
                if line.startswith("Description:"):
                    description = line.replace("Description:", "").strip()
                elif line.startswith("Hashtags:"):
                    hashtags = line.replace("Hashtags:", "").strip()
            
            if not description:
                description = "An artistic piece showcasing creative expression."
            if not hashtags:
                hashtags = "#art #creative"

            return description, hashtags

        except Exception as e:
            print(f"Error parsing GPT response: {str(e)}")
            return "An artistic piece", "#art"

gpt_service = GPTService()
