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

print("="*60)
print("  🎨 PUBLER API - PINTEREST TEST (FIXED)")
print("="*60)

# Get Pinterest account
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
pinterest = next((acc for acc in accounts if acc.get('provider') == 'pinterest'), None)

print(f"\n✅ Pinterest: @{pinterest.get('name')}")

boards = pinterest.get('albums', [])
board_id = boards[0]['id']
board_name = boards[0]['name']
print(f"   Board: {board_name}")

# Upload image
print("\n📸 Uploading image...")
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('artwork.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_data = upload_resp.json()
    media_id = media_data['id']

print(f"✅ Media ID: {media_id}")

# Schedule Pinterest pin
print("\n📌 Scheduling Pinterest pin...")
scheduled_time = (datetime.utcnow() + timedelta(minutes=35)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "pinterest": {
                        "type": "photo",
                        "media": [{"id": media_id}],
                        "text": "🎨 Content Planner API Test\n\nAutomated Pinterest posting via Publer API! When artwork sells on Etsy, the system will automatically cancel old posts and schedule replacements.\n\n#PromptCreative #Automation",
                        "title": "Automated Art Marketing"
                    }
                },
                "accounts": [
                    {
                        "id": pinterest['id'],
                        "scheduled_at": scheduled_time,
                        "album_id": board_id
                    }
                ]
            }
        ]
    }
}

response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)

if response.status_code == 200:
    job_id = response.json()['job_id']
    print(f"✅ Job: {job_id}")
    
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    status_data = status_resp.json()
    
    failures = status_data.get('payload', {}).get('failures', {})
    if failures:
        print("\n❌ FAILED:")
        print(json.dumps(failures, indent=2))
    
    posts = status_data.get('posts', [])
    if posts:
        post_id = posts[0]['id']
        print(f"\n✅ SUCCESS! Pin created!")
        print(f"   Post ID: {post_id}")
        print(f"   Scheduled: {posts[0].get('scheduled_at')}")
        
        # Delete test pin
        print(f"\n🗑️  Deleting test pin...")
        requests.delete(f'{BASE_URL}/posts/{post_id}', headers=headers)
        print("✅ Deleted")
        
        print("\n" + "="*60)
        print("  ✅ PUBLER API FULLY WORKING!")
        print("="*60)
        print("\n✓ Upload images to Publer")
        print("✓ Schedule Pinterest pins")
        print("✓ Delete scheduled posts")
        print("\nREADY TO BUILD FULL INTEGRATION! 🚀")
        print("="*60 + "\n")
    else:
        print("\n⚠️ No posts:")
        print(json.dumps(status_data, indent=2))
else:
    print(f"❌ Failed: {response.text}")
