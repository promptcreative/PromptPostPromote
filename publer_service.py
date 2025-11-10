import os
import requests
from datetime import datetime

class PublerAPI:
    """Publer API client for testing and integration"""
    
    def __init__(self):
        self.api_key = os.environ.get('PUBLER_API_KEY')
        self.workspace_id = os.environ.get('PUBLER_WORKSPACE_ID', '690d1b03a8e6a73f9973ffce')
        self.base_url = 'https://app.publer.com/api/v1'
        
        if not self.api_key:
            raise ValueError("PUBLER_API_KEY not found in environment variables")
    
    def _get_headers(self):
        """Get standard headers for API requests"""
        return {
            'Authorization': f'Bearer-API {self.api_key}',
            'Publer-Workspace-Id': self.workspace_id,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """Test API connection by fetching workspaces"""
        try:
            response = requests.get(
                f'{self.base_url}/workspaces',
                headers={'Authorization': f'Bearer-API {self.api_key}'}
            )
            response.raise_for_status()
            return {
                'success': True,
                'workspaces': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }
    
    def get_accounts(self):
        """Get connected social media accounts"""
        try:
            headers = self._get_headers()
            print(f"DEBUG: Requesting accounts with workspace_id: {self.workspace_id}")
            print(f"DEBUG: Headers: {headers}")
            
            response = requests.get(
                f'{self.base_url}/accounts',
                headers=headers
            )
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text[:500]}")
            
            response.raise_for_status()
            return {
                'success': True,
                'accounts': response.json()
            }
        except requests.exceptions.RequestException as e:
            error_details = {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
            print(f"DEBUG: Error getting accounts: {error_details}")
            return error_details
    
    def create_draft(self, text, account_ids=None, scheduled_time=None, is_public=False):
        """
        Create a draft post in Publer
        
        Args:
            text: Post content/caption
            account_ids: List of account IDs to post to (optional)
            scheduled_time: ISO format datetime string (optional)
            is_public: Whether draft is public or private (default: False)
        """
        try:
            payload = {
                'text': text,
                'is_public': is_public
            }
            
            if account_ids:
                payload['accounts'] = account_ids
            
            if scheduled_time:
                payload['scheduled_time'] = scheduled_time
            
            response = requests.post(
                f'{self.base_url}/posts/drafts',
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return {
                'success': True,
                'draft': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None)
            }
    
    def get_drafts(self):
        """Get all draft posts"""
        try:
            response = requests.get(
                f'{self.base_url}/posts/drafts',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return {
                'success': True,
                'drafts': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None)
            }
    
    def upload_media(self, file_path):
        """Upload media file to Publer"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f'{self.base_url}/media',
                    headers={'Authorization': f'Bearer-API {self.api_key}', 'Publer-Workspace-Id': self.workspace_id},
                    files=files
                )
            
            print(f"DEBUG: Upload response status: {response.status_code}")
            print(f"DEBUG: Upload response: {response.text}")
            
            response.raise_for_status()
            return {
                'success': True,
                'media': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
    
    def create_scheduled_draft(self, account_id, scheduled_time, text='', media_ids=None, network='instagram', is_public=False):
        """
        Create a scheduled draft post using Publer's bulk API
        
        Args:
            account_id: Social media account ID
            scheduled_time: ISO format datetime string (e.g., "2025-11-15T14:30:00Z")
            text: Post caption/description
            media_ids: List of media IDs from upload_media
            network: 'instagram' or 'pinterest'
            is_public: True for draft_public, False for draft_private
        """
        try:
            # Build media array
            media_array = []
            if media_ids:
                for media_id in media_ids:
                    media_array.append({
                        'id': media_id,
                        'type': 'image'
                    })
            
            # Build network content
            network_content = {
                'type': 'photo' if media_array else 'status',
                'text': text or ''
            }
            
            if media_array:
                network_content['media'] = media_array
            
            payload = {
                'bulk': {
                    'state': 'draft_public' if is_public else 'draft_private',
                    'posts': [
                        {
                            'networks': {
                                'default': network_content
                            },
                            'accounts': [
                                {
                                    'id': account_id,
                                    'scheduled_at': scheduled_time
                                }
                            ]
                        }
                    ]
                }
            }
            
            print(f"DEBUG: Creating draft with payload: {payload}")
            
            response = requests.post(
                f'{self.base_url}/posts/schedule',
                headers=self._get_headers(),
                json=payload
            )
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response: {response.text[:500]}")
            
            response.raise_for_status()
            return {
                'success': True,
                'draft': response.json()
            }
        except requests.exceptions.RequestException as e:
            error_result = {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
            print(f"DEBUG: Draft creation error: {error_result}")
            return error_result
