import os
import time
from openai import OpenAI
from typing import Tuple, Dict, Optional

class GPTService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum time between requests in seconds

    def _rate_limit(self):
        """Simple rate limiting implementation"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def generate_artwork_content(
        self, 
        category: str, 
        filename: str, 
        feedback: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate description and hashtags for artwork using GPT
        
        Args:
            category: The artwork category/title
            filename: Original filename of the artwork
            feedback: Optional feedback for content refinement
        
        Returns:
            Tuple of (description, hashtags)
        """
        self._rate_limit()

        # Construct the base prompt
        base_prompt = (
            f"Generate a creative and engaging description and relevant hashtags for an artwork.\n"
            f"Category/Title: {category}\n"
            f"Filename: {filename}\n"
        )

        # Add feedback to prompt if provided
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

            # Parse the response
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
            
            # Ensure we have valid content
            if not description:
                description = "An artistic piece showcasing creative expression."
            if not hashtags:
                hashtags = "#art #creative"

            return description, hashtags

        except Exception as e:
            print(f"Error parsing GPT response: {str(e)}")
            return "An artistic piece", "#art"

# Create a singleton instance
gpt_service = GPTService()
