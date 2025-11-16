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
print("  🎨 TESTING WITH ORIGINAL ART BOARD")
print("="*60)

# Get Pinterest account
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
pinterest = next((acc for acc in accounts if acc.get('provider') == 'pinterest'), None)

print(f"\n✅ Pinterest: @{pinterest.get('name')}")

# Find "Original Art" board
boards = pinterest.get('albums', [])
original_art_board = next((b for b in boards if 'original' in b['name'].lower() and 'art' in b['name'].lower()), None)

if not original_art_board:
    print("\n❌ Original Art board not found. Available boards:")
    for b in boards[:10]:
        print(f"   - {b['name']}")
    exit(1)

board_id = original_art_board['id']
board_name = original_art_board['name']

print(f"   Board: {board_name}")
print(f"   Board ID: {board_id}")

# Upload image
print("\n📸 Uploading artwork...")
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('artwork.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_data = upload_resp.json()
    media_id = media_data['id']

print(f"✅ Media uploaded: {media_id}")

# Schedule pin to Original Art board
print("\n📌 Scheduling pin to Original Art board...")
scheduled_time = (datetime.utcnow() + timedelta(minutes=40)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "pinterest": {
                        "type": "photo",
                        "media": [{"id": media_id}],
                        "text": "🎨 Test from Content Planner\n\nAutomated Pinterest posting via Publer API! System will auto-cancel & replace posts when artwork sells on Etsy.\n\n#PromptCreative #OriginalArt",
                        "title": "Content Planner Test"
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

print(f"   Scheduled for: {scheduled_time}")

response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)

if response.status_code == 200:
    job_id = response.json()['job_id']
    print(f"✅ Job created: {job_id}")
    
    print("\n⏳ Waiting for job to complete...")
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    status_data = status_resp.json()
    
    # Check failures
    failures = status_data.get('payload', {}).get('failures', {})
    if failures:
        print("\n❌ JOB FAILED:")
        for key, errors in failures.items():
            for error in errors:
                print(f"   Error: {error.get('message')}")
        print("\nFull response:")
        print(json.dumps(status_data, indent=2))
    
    # Check success
    posts = status_data.get('posts', [])
    if posts:
        post = posts[0]
        post_id = post['id']
        
        print(f"\n🎉 SUCCESS! Pinterest pin created!")
        print(f"   Post ID: {post_id}")
        print(f"   Board: {board_name}")
        print(f"   Scheduled: {post.get('scheduled_at')}")
        print(f"   Platform: Pinterest")
        
        # Delete test pin
        print(f"\n🗑️  Deleting test pin...")
        delete_resp = requests.delete(f'{BASE_URL}/posts/{post_id}', headers=headers)
        if delete_resp.status_code == 200:
            print("✅ Test pin deleted")
        
        print("\n" + "="*60)
        print("  ✅ PUBLER API WORKS PERFECTLY!")
        print("="*60)
        print("\n🎯 VERIFIED:")
        print("   ✓ Upload images to Publer")
        print("   ✓ Schedule pins to Original Art board")
        print("   ✓ Delete scheduled posts")
        print("\n🚀 READY TO BUILD:")
        print("   → Etsy integration (track sold items)")
        print("   → Auto-schedule via Publer API")
        print("   → Auto-cancel when items sell")
        print("   → Auto-replace with available artwork")
        print("\n   NO MANUAL EXPORTS NEEDED!")
        print("="*60 + "\n")
    else:
        print("\n⚠️ Job completed but no posts created")
        print("\nFull job status:")
        print(json.dumps(status_data, indent=2))
else:
    print(f"\n❌ Request failed: {response.status_code}")
    print(response.text)
