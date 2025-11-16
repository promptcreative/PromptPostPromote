import os
import requests
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
print("  📸 INSTAGRAM TEST - 1:55 PM EST")
print("="*60)

# Get Instagram account
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
instagram = next((acc for acc in accounts if acc.get('provider') == 'instagram'), None)

print(f"\n✅ Instagram: @{instagram.get('username')}")

# Upload image
print("\n📸 Uploading image...")
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('test.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_id = upload_resp.json()['id']

print(f"✅ Media ID: {media_id}")

# Schedule for EXACTLY 1:55 PM EST (18:55 UTC)
scheduled_time = "2025-11-16T18:55:00.000Z"

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "instagram": {
                        "type": "photo",
                        "media": [{"id": media_id}],
                        "text": "🎨 Instagram API Test - 1:55 PM EST\n\nContent Planner → Publer → Instagram\nAutomated posting works!\n\n#PromptCreative #Test"
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

print(f"\n📅 Scheduling Instagram post for: 1:55 PM EST (18:55 UTC)")

response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)

if response.status_code == 200:
    job_id = response.json()['job_id']
    print(f"✅ Job created: {job_id}")
    
    print("\n⏳ Checking job status...")
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    status_data = status_resp.json()
    
    failures = status_data.get('payload', {}).get('failures', {})
    if failures:
        print("\n❌ FAILED:")
        print(json.dumps(failures, indent=2))
    else:
        print("\n✅ SUCCESS! Post created in Publer")
        print("\n📱 Check your Publer dashboard - should see:")
        print("   Platform: Instagram")
        print("   Time: 1:55 PM EST (18:55 UTC)")
        print("   Status: Scheduled")
        print("\n⏰ Will post in ~4 minutes!")
        print("="*60)
else:
    print(f"❌ Failed: {response.text}")
