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
print("  🎨 TESTING PUBLER API WITH PINTEREST")
print("="*60)

# Get Pinterest account
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
pinterest = next((acc for acc in accounts if acc.get('provider') == 'pinterest'), None)

if not pinterest:
    print("❌ No Pinterest account found")
    exit(1)

print(f"\n✅ Pinterest account: @{pinterest.get('name')}")
print(f"   Boards available: {len(pinterest.get('albums', []))}")

# Get first board
boards = pinterest.get('albums', [])
if not boards:
    print("❌ No Pinterest boards found")
    exit(1)

board_id = boards[0]['id']
board_name = boards[0]['name']
print(f"   Using board: {board_name}")

# Upload image
print("\n📸 Uploading image...")
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('artwork.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_data = upload_resp.json()
    media_id = media_data['id']

print(f"✅ Image uploaded: {media_id}")

# Schedule Pinterest pin
print("\n📌 Scheduling Pinterest pin...")
scheduled_time = (datetime.utcnow() + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "pinterest": {
                        "type": "pin",
                        "media": [{"id": media_id}],
                        "text": "Content Planner API Test - Automated Pinterest posting when items sell on Etsy!",
                        "title": "Automated Art Marketing",
                        "board": board_id,
                        "link": "https://promptcreative.co"
                    }
                },
                "accounts": [
                    {
                        "id": pinterest['id'],
                        "scheduled_at": scheduled_time
                    }
                ]
            }
        ]
    }
}

print(f"   Scheduled for: {scheduled_time}")
print(f"   Board: {board_name}")

response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    job_id = data['job_id']
    print(f"✅ Job created: {job_id}")
    
    print("\n⏳ Waiting for job...")
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    status_data = status_resp.json()
    
    print("\n=== JOB STATUS ===")
    print(json.dumps(status_data, indent=2))
    
    # Check results
    failures = status_data.get('payload', {}).get('failures', {})
    if failures:
        print("\n❌ FAILED")
        for key, errors in failures.items():
            for error in errors:
                print(f"   Error: {error.get('message')}")
    
    posts = status_data.get('posts', [])
    if posts:
        post = posts[0]
        post_id = post['id']
        print("\n✅ SUCCESS! Pinterest pin created!")
        print(f"   Post ID: {post_id}")
        print(f"   Scheduled: {post.get('scheduled_at')}")
        
        # Now delete it
        print("\n🗑️  Deleting test pin...")
        delete_resp = requests.delete(f'{BASE_URL}/posts/{post_id}', headers=headers)
        if delete_resp.status_code == 200:
            print("✅ Test pin deleted")
            
            print("\n" + "="*60)
            print("  ✅ PUBLER API WORKS!")
            print("="*60)
            print("\nWe can successfully:")
            print("  ✓ Upload images")
            print("  ✓ Schedule Pinterest pins")
            print("  ✓ Delete scheduled posts")
            print("\nReady to build full integration!")
            print("="*60 + "\n")
    else:
        print("\n⚠️ No posts created")

else:
    print(f"❌ Request failed: {response.status_code}")
    print(response.text)
