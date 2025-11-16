import os
import requests
from datetime import datetime, timedelta
import json
import time

API_KEY = os.getenv('PUBLER_API_KEY')
WORKSPACE_ID = os.getenv('PUBLER_WORKSPACE_ID')
BASE_URL = 'https://app.publer.com/api/v1'

headers = {
    'Authorization': f'Bearer-API {API_KEY}',
    'Publer-Workspace-Id': WORKSPACE_ID,
    'Content-Type': 'application/json'
}

# Get Instagram account
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
instagram = next((acc for acc in accounts if acc.get('provider') == 'instagram'), None)

# Upload image
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('test.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_data = upload_resp.json()
    media_id = media_data['id']

print(f"Media uploaded: {media_id}")
print(f"Instagram account: {instagram['id']}")

# Try scheduling with minimal payload
scheduled_time = (datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "instagram": {
                        "type": "photo",
                        "media": [{"id": media_id}],
                        "text": "Test post from Content Planner API"
                    }
                },
                "accounts": [
                    {
                        "id": instagram['id'],
                        "scheduled_at": scheduled_time
                    }
                ]
            }
        ]
    }
}

print("\n=== REQUEST PAYLOAD ===")
print(json.dumps(payload, indent=2))

response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)
print(f"\n=== RESPONSE STATUS: {response.status_code} ===")
print(response.text)

if response.status_code == 200:
    data = response.json()
    job_id = data.get('job_id')
    
    print(f"\nJob ID: {job_id}")
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    print("\n=== FULL JOB STATUS ===")
    print(json.dumps(status_resp.json(), indent=2))
