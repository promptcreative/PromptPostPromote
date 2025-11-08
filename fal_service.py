import os
import requests
import time
from typing import Optional, Dict

class FalService:
    """Service for generating videos using fal.ai Pika 2.2 API"""
    
    def __init__(self):
        self.api_key = os.environ.get('FAL_API_KEY')
        if not self.api_key:
            raise ValueError("FAL_API_KEY not found in environment")
        
        self.base_url = "https://queue.fal.run/fal-ai/pika/v2.2/image-to-video"
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_video(self, image_url: str, prompt: str = "camera slowly zooming in", 
                      resolution: str = "720p", duration: int = 5) -> Optional[Dict]:
        """Generate a video from an image using Pika 2.2
        
        Args:
            image_url: Public URL of the artwork image
            prompt: Motion prompt describing the desired camera movement/effect
            resolution: Video resolution (720p or 1080p)
            duration: Video duration in seconds (3-5)
            
        Returns:
            Dict with video_url and metadata, or None if failed
        """
        payload = {
            "image_url": image_url,
            "prompt": prompt,
            "resolution": resolution,
            "duration": duration
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            request_id = data.get('request_id')
            if not request_id:
                print("No request_id in response")
                return None
            
            return self._poll_for_result(request_id)
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating video: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None
    
    def _poll_for_result(self, request_id: str, max_wait: int = 300, poll_interval: int = 5) -> Optional[Dict]:
        """Poll fal.ai for video generation result
        
        Args:
            request_id: The request ID from the initial API call
            max_wait: Maximum time to wait in seconds
            poll_interval: Seconds between polling requests
            
        Returns:
            Dict with video_url and metadata, or None if failed
        """
        status_url = f"https://queue.fal.run/fal-ai/pika/v2.2/image-to-video/requests/{request_id}"
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(status_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                status = data.get('status')
                
                if status == 'COMPLETED':
                    output = data.get('output', {})
                    video_url = output.get('video', {}).get('url')
                    
                    if video_url:
                        return {
                            'video_url': video_url,
                            'duration': output.get('duration'),
                            'resolution': output.get('resolution'),
                            'prompt': data.get('input', {}).get('prompt')
                        }
                    else:
                        print("Video generation completed but no URL found")
                        return None
                
                elif status == 'FAILED':
                    error = data.get('error', 'Unknown error')
                    print(f"Video generation failed: {error}")
                    return None
                
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    time.sleep(poll_interval)
                    continue
                
                else:
                    print(f"Unknown status: {status}")
                    time.sleep(poll_interval)
                    
            except requests.exceptions.RequestException as e:
                print(f"Error polling for result: {e}")
                time.sleep(poll_interval)
        
        print(f"Video generation timed out after {max_wait} seconds")
        return None
