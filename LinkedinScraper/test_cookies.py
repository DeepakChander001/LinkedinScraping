import json
import os
   
print("Current directory:", os.getcwd())
print("Files in current directory:", os.listdir('.'))
   
try:
    with open('linkedin_cookies.json', 'r') as f:
        cookies = json.load(f)
    print(f"Cookies loaded successfully. Found {len(cookies)} cookies.")
    print("Essential cookies present:")
    print("li_at:", any(c['name'] == 'li_at' for c in cookies))
    print("JSESSIONID:", any(c['name'] == 'JSESSIONID' for c in cookies))
    print("lidc:", any(c['name'] == 'lidc' for c in cookies))
except Exception as e:
    print(f"Error loading cookies: {e}")