import os
import requests
from datetime import datetime

class PublerAPI:
    """Publer API client for testing and integration"""
    
    def __init__(self):
        self.api_key = os.environ.get('PUBLER_API_KEY')
        self.workspace_id = os.environ.get('PUBLER_WORKSPACE_ID')
        self.base_url = 'https://app.publer.com/api/v1'
        
        if not self.api_key:
            raise ValueError("PUBLER_API_KEY not found in environment variables")
        if not self.workspace_id:
            raise ValueError("PUBLER_WORKSPACE_ID not found in environment variables")
    
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
            response = requests.get(
                f'{self.base_url}/accounts',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return {
                'success': True,
                'accounts': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None)
            }
    
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
