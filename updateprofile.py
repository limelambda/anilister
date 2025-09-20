import requests
import json
import time

def get_score(animetxt):
    if '!!!!' in animetxt:
        return 100
    if '!!!' in animetxt:
        return 90
    if '!!' in animetxt:
        return 80
    return None

with open('env.json') as env:
    env = json.loads(env.read())
    CLIENT_ID = env['client_id'] 
    CLIENT_SECRET = env['client_secret']  # Required for token exchange

# Get authorization code from AniList PIN flow
auth_url = f"https://anilist.co/api/v2/oauth/authorize?client_id={CLIENT_ID}&redirect_uri=https://anilist.co/api/v2/oauth/pin&response_type=code"
print(f"Please visit this URL in your browser: {auth_url}")
print("Log in, copy the authorization code from the page, and enter it below.")
auth_code = input("Enter the authorization code: ").strip()

# Exchange authorization code for access token
token_url = "https://anilist.co/api/v2/oauth/token"
token_data = {
    'grant_type': 'authorization_code',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': 'https://anilist.co/api/v2/oauth/pin',
    'code': auth_code,
}

# Try form-encoded data first (more common for OAuth)
print("Exchanging authorization code for access token...")
token_response = requests.post(token_url, data=token_data)

if token_response.status_code != 200:
    print(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
    print("Trying with JSON format...")
    # Fallback to JSON if form-encoded fails
    token_response = requests.post(token_url, json=token_data, headers={'Content-Type': 'application/json'})
    
    if token_response.status_code != 200:
        print(f"Token exchange failed again: {token_response.status_code} - {token_response.text}")
        exit(1)

token_json = token_response.json()
access_token = token_json['access_token']
print("Successfully obtained access token!")

# Use access token for GraphQL requests
graphql_url = "https://graphql.anilist.co"
graphql_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

mutation = '''mutation ($mediaId: Int, $score: Float, $status: MediaListStatus) {
  SaveMediaListEntry(
    mediaId: $mediaId
    score: $score
    status: $status
  ) {
    id
    score(format: POINT_100)
    status
    updatedAt
  }
}'''

with open('anime.json', encoding='utf-8') as anime_anilist_file:
    anime_anilist = json.loads(anime_anilist_file.read())

with open('anime.txt', encoding='utf-8') as anime_txtlist_file:
    anime_txtlist = anime_txtlist_file.readlines()

for anime_ani, anime_txt in zip(anime_anilist, anime_txtlist):
    score = get_score(anime_txt)
    mediaId = anime_ani['anilist_id']

    variables = {
        "mediaId": mediaId,
        "status": "COMPLETED",
    }
    
    # Only add score if one was found
    if score is not None:
        variables["score"] = score
        print(f"Updating {anime_ani.get('title', 'Unknown')} - COMPLETED with score {score}")
    else:
        print(f"Updating {anime_ani.get('title', 'Unknown')} - COMPLETED without score")

    payload = {
        "query": mutation,
        "variables": variables,
    }

    # Handle rate limiting
    while True:
        response = requests.post(graphql_url, json=payload, headers=graphql_headers)
        if response.status_code != 429:
            break
        wait_time = response.headers.get('Retry-After', 60)  # Default to 60s if not specified
        print(f'Rate limited for {wait_time}s')
        time.sleep(int(wait_time) + 1)

    # Handle response
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            print("Success! Updated entry:")
            print(json.dumps(data['data']['SaveMediaListEntry'], indent=2))
    else:
        print(f"HTTP Error {response.status_code}: {response.text}")
        
    # Small delay to avoid hitting rate limits
    time.sleep(0.5)