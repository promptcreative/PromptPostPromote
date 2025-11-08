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
        
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error reading image: {e}")
            return self._generate_fallback_content(painting_name, platform)
        
        platform_prompts = {
            "instagram": """Analyze this artwork and create Instagram content:
1. A captivating caption (2-3 sentences, engaging and authentic)
2. Instagram first comment with relevant hashtags (20-30 hashtags including art style, colors, medium, mood)
3. SEO-friendly title
4. SEO description
5. SEO tags (comma-separated keywords)

Format your response as:
CAPTION: [caption text]
FIRST_COMMENT: [hashtags only]
SEO_TITLE: [title]
SEO_DESCRIPTION: [description]
SEO_TAGS: [tags]""",
            
            "pinterest": """Analyze this artwork and create Pinterest content:
1. Pinterest description (detailed, 300-500 chars, keyword-rich for search)
2. Pinterest board category suggestion
3. Link URL suggestion (where to link this pin)
4. SEO title
5. SEO description
6. SEO tags (comma-separated keywords)
7. Alt text for accessibility

Format your response as:
PINTEREST_DESC: [description]
PINTEREST_BOARD: [board name]
PINTEREST_LINK: [suggested link]
SEO_TITLE: [title]
SEO_DESCRIPTION: [description]
SEO_TAGS: [tags]
ALT_TEXT: [accessibility description]""",
            
            "etsy": """Analyze this artwork and create Etsy listing content:
1. Listing title (engaging, keyword-rich, under 140 chars)
2. Full description (detailed, 2-3 paragraphs about the artwork, style, colors, mood, what makes it special)
3. SEO tags (13 relevant keywords/phrases for Etsy search)
4. Suggested price range
5. Alt text for accessibility

Format your response as:
ETSY_TITLE: [title]
ETSY_DESC: [full description]
SEO_TAGS: [13 tags separated by commas]
ETSY_PRICE: [suggested price range like "$25-50"]
ALT_TEXT: [accessibility description]""",
            
            "all": """Analyze this artwork and create comprehensive content for ALL platforms (Instagram, Pinterest, Etsy):

INSTAGRAM:
- Caption (2-3 sentences)
- First comment hashtags (20-30 hashtags)

PINTEREST:
- Description (keyword-rich, 300-500 chars)
- Board category
- Link suggestion

ETSY:
- Listing title (under 140 chars)
- Full description (2-3 paragraphs)
- Price range suggestion

GENERAL:
- SEO title
- SEO description
- SEO tags (comprehensive list)
- Alt text for accessibility
- General text/caption

Format your response as:
IG_CAPTION: [caption]
IG_FIRST_COMMENT: [hashtags]
PINTEREST_DESC: [description]
PINTEREST_BOARD: [board]
PINTEREST_LINK: [link]
ETSY_TITLE: [title]
ETSY_DESC: [description]
ETSY_PRICE: [price]
SEO_TITLE: [title]
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
        
        prompt = f"{artwork_details}\n\n{prompt}\n\nIMPORTANT: Incorporate the size, materials, and artist's personal note into your descriptions to make the content unique and authentic."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert art curator and digital marketing specialist. Analyze artwork images and create compelling, SEO-optimized content for social media and e-commerce platforms."
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
        
        return result

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
