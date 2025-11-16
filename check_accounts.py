import os
import requests
import json

API_KEY = os.getenv('PUBLER_API_KEY')
WORKSPACE_ID = os.getenv('PUBLER_WORKSPACE_ID')
BASE_URL = 'https://app.publer.com/api/v1'

headers = {
    'Authorization': f'Bearer-API {API_KEY}',
    'Publer-Workspace-Id': WORKSPACE_ID,
    'Content-Type': 'application/json'
}

print("="*60)
print("  CHECKING PUBLER ACCOUNTS IN DETAIL")
print("="*60 + "\n")

response = requests.get(f'{BASE_URL}/accounts', headers=headers)

if response.status_code == 200:
    accounts = response.json()
    print(f"Found {len(accounts)} account(s)\n")
    
    for i, acc in enumerate(accounts, 1):
        print(f"\n{'='*60}")
        print(f"ACCOUNT {i}:")
        print('='*60)
        print(json.dumps(acc, indent=2))
        print()
else:
    print(f"Failed: {response.text}")
