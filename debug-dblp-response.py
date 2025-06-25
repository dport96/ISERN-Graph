#!/usr/bin/env python3
"""
Debug script to examine DBLP author search response structure
"""

import requests
import xmltodict
import json
from urllib.parse import quote

def debug_dblp_response(author_name):
    try:
        encoded_name = quote(author_name)
        url = f"https://dblp.org/search/author/api?q={encoded_name}&format=xml&h=3"
        
        print(f"Testing: {author_name}")
        print(f"URL: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        print("Raw XML:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        # Parse XML response
        data = xmltodict.parse(response.content)
        
        print("\nParsed structure:")
        print(json.dumps(data, indent=2)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2))
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    debug_dblp_response("Dan Port")
