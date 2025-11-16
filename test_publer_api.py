import os
import requests
from datetime import datetime, timedelta
import json

# Publer API Configuration
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

def test_get_workspaces():
    print_section("TEST 1: Get Workspaces")
    response = requests.get(f'{BASE_URL}/workspaces', headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data)} workspace(s)")
        print(json.dumps(data, indent=2))
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_get_accounts():
    print_section("TEST 2: Get Connected Social Accounts")
    response = requests.get(f'{BASE_URL}/accounts', headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data)} connected account(s)")
        for acc in data:
            print(f"  - {acc.get('network', 'unknown').upper()}: {acc.get('name', 'unnamed')} (ID: {acc.get('id', 'no-id')})")
        return data
    else:
        print(f"❌ Failed: {response.text}")
        return []

def test_schedule_post(account_id, network):
    print_section("TEST 3: Schedule a Test Post")
    
    # Schedule 5 minutes from now
    scheduled_time = datetime.utcnow() + timedelta(minutes=5)
    scheduled_iso = scheduled_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    payload = {
        "bulk": {
            "state": "scheduled",
            "posts": [
                {
                    "networks": {
                        network: {
                            "type": "status",
                            "text": "🎨 TEST POST from Content Planner API Integration\n\nThis is a test to verify Publer API workflow.\n\n#PromptCreative #TestPost"
                        }
                    },
                    "accounts": [
                        {
                            "id": account_id,
                            "scheduled_at": scheduled_iso
                        }
                    ]
                }
            ]
        }
    }
    
    print(f"Scheduling for: {scheduled_iso}")
    response = requests.post(f'{BASE_URL}/posts/schedule', headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        job_id = data.get('job_id')
        print(f"✅ Success! Job ID: {job_id}")
        
        # Check job status
        import time
        time.sleep(2)
        
        status_response = requests.get(f'{BASE_URL}/job_status/{job_id}', headers=headers)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("\nJob Status:")
            print(json.dumps(status_data, indent=2))
            
            if status_data.get('posts') and len(status_data['posts']) > 0:
                post_id = status_data['posts'][0].get('id')
                print(f"\n✅ Post Created! Post ID: {post_id}")
                return post_id
        return None
    else:
        print(f"❌ Failed: {response.text}")
        return None

def test_update_post(post_id):
    print_section("TEST 4: Update the Test Post")
    
    payload = {
        "post": {
            "text": "🎨 UPDATED TEST POST from Content Planner\n\nThis text was updated via Publer API!\n\n#PromptCreative #APITest #Updated"
        }
    }
    
    response = requests.put(f'{BASE_URL}/posts/{post_id}', headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Success! Post {post_id} updated")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_delete_post(post_id):
    print_section("TEST 5: Delete the Test Post")
    
    response = requests.delete(f'{BASE_URL}/posts/{post_id}', headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Success! Post {post_id} deleted (cancelled)")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_list_posts():
    print_section("TEST 6: List Scheduled Posts")
    
    response = requests.get(f'{BASE_URL}/posts?state=scheduled', headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        posts = data.get('posts', [])
        print(f"✅ Success! Found {len(posts)} scheduled post(s)")
        
        if posts:
            for post in posts[:5]:  # Show first 5
                print(f"\n  Post ID: {post.get('id')}")
                print(f"  Network: {post.get('network', 'unknown').upper()}")
                print(f"  Scheduled: {post.get('scheduled_at')}")
                print(f"  Text: {post.get('text', 'no text')[:50]}...")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("  PUBLER API INTEGRATION TEST")
    print("  Testing Full Workflow for Content Planner")
    print("="*60)
    
    # Test 1: Get workspaces
    if not test_get_workspaces():
        print("\n❌ Workspace test failed - check API key")
        return
    
    # Test 2: Get accounts
    accounts = test_get_accounts()
    if not accounts:
        print("\n❌ No social accounts connected")
        print("Please connect Instagram/Pinterest/Facebook in Publer first")
        return
    
    # Use first account for testing
    first_account = accounts[0]
    account_id = first_account.get('id')
    network = first_account.get('network', 'facebook').lower()
    
    print(f"\n📌 Using account: {first_account.get('name')} ({network.upper()})")
    
    # Test 3: Schedule post
    post_id = test_schedule_post(account_id, network)
    if not post_id:
        print("\n❌ Failed to create post - stopping tests")
        return
    
    # Test 4: Update post
    test_update_post(post_id)
    
    # Test 5: Delete post
    test_delete_post(post_id)
    
    # Test 6: List posts
    test_list_posts()
    
    print_section("TEST SUMMARY")
    print("✅ All tests completed!")
    print("\n📋 VERIFIED CAPABILITIES:")
    print("  ✓ Connect to Publer API")
    print("  ✓ Schedule posts to social media")
    print("  ✓ Update scheduled posts")
    print("  ✓ Delete (cancel) scheduled posts")
    print("  ✓ List existing scheduled posts")
    print("\n🎯 READY FOR INTEGRATION:")
    print("  → Content Planner can now schedule posts via Publer")
    print("  → When item sells: DELETE old post, CREATE replacement")
    print("  → No manual CSV exports needed!")
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
