import requests
import json
import re
from bs4 import BeautifulSoup
import os

# Create directory for saved data
if not os.path.exists('debug_output'):
    os.makedirs('debug_output')

# Load cookies from file
try:
    with open('linkedin_cookies.json', 'r') as f:
        cookies = json.load(f)
    print(f"Loaded {len(cookies)} cookies")
except Exception as e:
    print(f"Error loading cookies: {e}")
    cookies = []

# Convert cookies to dict format
cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
essential_cookies = ['li_at', 'JSESSIONID', 'lidc']
for cookie in essential_cookies:
    if cookie in cookie_dict:
        print(f"Found essential cookie: {cookie}")
    else:
        print(f"Missing essential cookie: {cookie}")

# Define headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.linkedin.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

# Make a request to the LinkedIn search page
search_term = "AI Engineer"
url = f"https://www.linkedin.com/search/results/people/?keywords={search_term.replace(' ', '%20')}"
print(f"Requesting URL: {url}")

try:
    response = requests.get(url, cookies=cookie_dict, headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response URL: {response.url}")  # Check if redirected
    
    # Save the full response
    with open('debug_output/linkedin_full_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved full response to debug_output/linkedin_full_response.html")
    
    # Check if logged in or redirected to login page
    if "login" in response.url:
        print("PROBLEM: Redirected to login page. Your cookies are not working.")
    else:
        print("SUCCESS: Not redirected to login page.")
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for profile links
    profile_links = []
    
    # Look for links to profiles
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/in/' in href:
            profile_links.append(href)
    
    # Save list of found profile links
    with open('debug_output/profile_links.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(profile_links))
    
    print(f"Found {len(profile_links)} profile links")
    if profile_links:
        print("Example links:")
        for link in profile_links[:5]:
            print(f"  - {link}")
    
    # Check first profile if any were found
    if profile_links:
        first_profile = profile_links[0]
        if not first_profile.startswith('http'):
            first_profile = f"https://www.linkedin.com{first_profile}"
        
        print(f"\nChecking first profile: {first_profile}")
        profile_response = requests.get(first_profile, cookies=cookie_dict, headers=headers)
        print(f"Profile response status: {profile_response.status_code}")
        
        # Save the profile response
        with open('debug_output/profile_response.html', 'w', encoding='utf-8') as f:
            f.write(profile_response.text)
        print("Saved profile response to debug_output/profile_response.html")
        
        # Extract some basic info
        profile_soup = BeautifulSoup(profile_response.text, 'html.parser')
        name = profile_soup.find('h1')
        if name:
            print(f"Found name: {name.text.strip()}")
        else:
            print("Could not find name")

except Exception as e:
    print(f"Error: {e}")

print("\nDebugging complete. Check the debug_output directory for the saved HTML files.")
print("If LinkedIn is redirecting to login, your cookies are invalid or expired.")
print("If no profile links were found, LinkedIn might be using JavaScript to load the content or using different HTML structure.") 