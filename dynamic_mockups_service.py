import os
import requests
from typing import List, Dict, Optional

class DynamicMockupsService:
    """Service for generating wall art mockups using Dynamic Mockups API"""
    
    def __init__(self):
        self.api_key = os.environ.get('DYNAMIC_MOCKUPS_API_KEY')
        if not self.api_key:
            raise ValueError("DYNAMIC_MOCKUPS_API_KEY not found in environment")
        
        self.base_url = "https://api.dynamicmockups.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_templates(self, category: str = "wall-art", limit: int = 50) -> List[Dict]:
        """Fetch available mockup templates
        
        Args:
            category: Template category (wall-art, frames, posters, etc.)
            limit: Maximum number of templates to return
            
        Returns:
            List of template dictionaries with id, name, preview_url
        """
        try:
            response = requests.get(
                f"{self.base_url}/templates",
                headers=self.headers,
                params={"category": category, "limit": limit},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get('templates', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching templates: {e}")
            return []
    
    def generate_mockup(self, image_url: str, template_id: str, additional_params: Optional[Dict] = None) -> Optional[str]:
        """Generate a mockup for an artwork image
        
        Args:
            image_url: Public URL of the artwork image
            template_id: ID of the mockup template to use
            additional_params: Optional parameters like background_color, frame_color, etc.
            
        Returns:
            URL of the generated mockup image, or None if failed
        """
        payload = {
            "template_id": template_id,
            "design_url": image_url
        }
        
        if additional_params:
            payload.update(additional_params)
        
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            mockup_url = data.get('mockup_url') or data.get('url')
            return mockup_url
        except requests.exceptions.RequestException as e:
            print(f"Error generating mockup: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None
    
    def generate_multiple_mockups(self, image_url: str, template_ids: List[str]) -> List[Dict]:
        """Generate multiple mockups for an artwork using different templates
        
        Args:
            image_url: Public URL of the artwork image
            template_ids: List of template IDs to use
            
        Returns:
            List of dicts with template_id and mockup_url
        """
        results = []
        for template_id in template_ids:
            mockup_url = self.generate_mockup(image_url, template_id)
            if mockup_url:
                results.append({
                    'template_id': template_id,
                    'mockup_url': mockup_url
                })
        return results
