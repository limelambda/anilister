import requests
import json
import time

INPUT_FILE = 'anime.txt'
OUTPUT_FILE = 'anime.json'

def search_anime(title: str):
    """Search for anime by title and return the top match's ID."""
    url = "https://graphql.anilist.co"
    headers = {
        # "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    query = '''query ($search: String, $page: Int, $perPage: Int) {
    Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME) {
        id
        title {
        romaji
        english
        }
        format
        status
    }
    }
}'''
    
    variables = {
        "search": title,
        "page": 1,
        "perPage": 5,  # Top 5 results for better matching if needed
    }
    
    payload = {"query": query, "variables": variables}
    
    while True:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 429:
            break
        wait_time = response.headers.get('Retry-After')
        print(f'Rate limited for {wait_time}s')
        time.sleep(int(wait_time)+1)
    
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    data = response.json()
    if "errors" in data:
        return {"error": data["errors"]}
    
    media_list = data["data"]["Page"]["media"]
    if not media_list:
        return {
            "title": title,
            "anilist_id": None,
            "matched_title": None,
            "format": None,
            "status": None,
        }
    
    # Return the first (top) match
    top_match = media_list[0]
    return {
        "title": title,
        "anilist_id": top_match["id"],
        "matched_title": top_match["title"]["english"],
        "format": top_match["format"],
        "status": top_match["status"],
    }

def main():
    #get_access_token()
    #
    #if not ACCESS_TOKEN:
    #    print("Failed to get access token.")
    #    return
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            titles = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File {INPUT_FILE} not found. Create it with anime titles.")
        return
    
    results = []
    for title in titles:
        title = title.split(' !!')[0].split(' S1')[0].split(' (Movie)')[0]
        print(f"Searching for: {title}")
        result = search_anime(title)
        results.append(result)
        print(f"Result: {result}")
    
    # Save results to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nBatch complete! Results saved to {OUTPUT_FILE}")
    print("Example output format:")
    print(json.dumps(results[:2], indent=2))  # Print first two for preview

if __name__ == "__main__":
    main()