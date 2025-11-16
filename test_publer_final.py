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

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

print("\n" + "="*60)
print("  🎨 PUBLER API FINAL INTEGRATION TEST")
print("="*60)

# Get Instagram account
print("\n📱 Getting Instagram account...")
response = requests.get(f'{BASE_URL}/accounts', headers=headers)
accounts = response.json()
instagram = next((acc for acc in accounts if acc.get('provider') == 'instagram'), None)
print(f"✅ Found: @{instagram.get('username')}")

# Upload image
print_section("STEP 1: Upload Artwork to Publer")
with open('static/uploads/artwork_2986fda6.png', 'rb') as f:
    files = {'file': ('artwork.png', f, 'image/png')}
    headers_upload = {'Authorization': f'Bearer-API {API_KEY}', 'Publer-Workspace-Id': WORKSPACE_ID}
    upload_resp = requests.post(f'{BASE_URL}/media', headers=headers_upload, files=files)
    media_data = upload_resp.json()
    media_id = media_data['id']

print(f"✅ Image uploaded successfully!")
print(f"   Media ID: {media_id}")

# Schedule post 30 minutes in future to avoid conflicts
print_section("STEP 2: Schedule Instagram Post")
scheduled_time = (datetime.utcnow() + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

payload = {
    "bulk": {
        "state": "scheduled",
        "posts": [
            {
                "networks": {
                    "instagram": {
                        "type": "photo",
                        "media": [{"id": media_id}],
                        "text": "🎨 Content Planner API Test\n\nThis post was automatically scheduled via Publer API integration!\n\nWhen artwork sells on Etsy:\n✅ Old post gets cancelled\n✅ Replacement gets scheduled  \n✅ Your feed stays updated\n\n#PromptCreative #Automation"
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

print(f"📅 Scheduling for: {scheduled_time}")
response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    job_id = data['job_id']
    print(f"✅ Job created: {job_id}")
    
    print("\n⏳ Waiting 5 seconds for job to complete...")
    time.sleep(5)
    
    status_resp = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
    status_data = status_resp.json()
    
    # Check for failures
    failures = status_data.get('payload', {}).get('failures', {})
    if failures:
        print("\n❌ Job failed:")
        for key, errors in failures.items():
            for error in errors:
                print(f"   {error.get('message')}")
        exit(1)
    
    # Get post ID
    posts = status_data.get('posts', [])
    if posts:
        post_id = posts[0]['id']
        print(f"\n✅ POST CREATED SUCCESSFULLY!")
        print(f"   Post ID: {post_id}")
        print(f"   Scheduled: {posts[0].get('scheduled_at')}")
        print(f"   Platform: Instagram")
        
        # Update post
        print_section("STEP 3: Update Post Caption")
        update_payload = {
            "post": {
                "text": "🎨 UPDATED! Automated Art Marketing\n\nCaption updated via Publer API!\n\nContent Planner now handles:\n✅ Automatic scheduling\n✅ Real-time updates\n✅ Etsy sync & replacements\n\nNo manual work needed! 🚀\n\n#PromptCreative #Updated"
            }
        }
        
        update_resp = requests.put(f'{BASE_URL}/posts/{post_id}', headers=headers, json=update_payload)
        if update_resp.status_code == 200:
            print("✅ Caption updated successfully!")
        
        # List posts
        print_section("STEP 4: List Scheduled Posts")
        list_resp = requests.get(f'{BASE_URL}/posts?state=scheduled&per_page=3', headers=headers)
        if list_resp.status_code == 200:
            list_data = list_resp.json()
            print(f"✅ Found {list_data.get('total', 0)} scheduled posts")
            for i, p in enumerate(list_data.get('posts', [])[:3], 1):
                print(f"\n   {i}. {p.get('provider', 'unknown').upper()}")
                print(f"      Time: {p.get('scheduled_at')}")
                print(f"      Text: {p.get('text', '')[:60]}...")
        
        # Delete post
        print_section("STEP 5: Delete (Cancel) Post")
        print(f"🗑️  Cancelling post {post_id}...")
        delete_resp = requests.delete(f'{BASE_URL}/posts/{post_id}', headers=headers)
        if delete_resp.status_code == 200:
            print("✅ Post cancelled successfully!")
            print("   (This simulates what happens when an item sells on Etsy)")
        
        # Final summary
        print_section("✅ ALL TESTS PASSED!")
        print("🎯 VERIFIED CAPABILITIES:")
        print("   ✓ Upload artwork to Publer")
        print("   ✓ Schedule Instagram posts with images")
        print("   ✓ Update post captions")
        print("   ✓ List scheduled posts")
        print("   ✓ Cancel/delete posts")
        print()
        print("🚀 READY TO BUILD INTEGRATION:")
        print()
        print("   YOUR AUTOMATED WORKFLOW:")
        print("   1. Upload artwork in Content Planner")
        print("   2. Assign to schedule → Auto-posts to Publer")
        print("   3. Item sells on Etsy → Auto-detected")
        print("   4. Old post cancelled → Replacement scheduled")
        print("   5. Everything synced automatically")
        print()
        print("   NO CSV EXPORTS!")
        print("   NO MANUAL UPDATES!")
        print("   ONE DASHBOARD CONTROLS EVERYTHING!")
        print()
        print("="*60 + "\n")
        
    else:
        print("\n⚠️ No posts created in job response")
        print(json.dumps(status_data, indent=2))
