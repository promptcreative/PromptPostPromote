import os
import requests
from datetime import datetime


class PublerAPI:

    def __init__(self):
        self.api_key = os.environ.get('PUBLER_API_KEY')
        self.workspace_id = os.environ.get('PUBLER_WORKSPACE_ID', '')
        self.base_url = 'https://app.publer.com/api/v1'

        if not self.api_key:
            raise ValueError("PUBLER_API_KEY not found in environment variables")

    def _get_headers(self):
        headers = {
            'Authorization': f'Bearer-API {self.api_key}',
            'Content-Type': 'application/json'
        }
        if self.workspace_id:
            headers['Publer-Workspace-Id'] = self.workspace_id
        return headers

    def test_connection(self):
        try:
            response = requests.get(
                f'{self.base_url}/workspaces',
                headers={'Authorization': f'Bearer-API {self.api_key}'}
            )
            response.raise_for_status()
            return {'success': True, 'workspaces': response.json()}
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }

    def get_accounts(self):
        try:
            response = requests.get(
                f'{self.base_url}/accounts',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return {'success': True, 'accounts': response.json()}
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }

    def create_draft(self, text, account_ids=None, scheduled_time=None, is_public=False):
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
            return {'success': True, 'draft': response.json()}
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }

    def delete_post(self, post_id):
        try:
            response = requests.delete(
                f'{self.base_url}/posts/{post_id}',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return {'success': True, 'post_id': post_id}
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'post_id': post_id,
                'status_code': getattr(e.response, 'status_code', None)
            }
