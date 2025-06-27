#!/usr/bin/env python3
"""
ISERN Members Scraper

This script scrapes the ISERN members and their organizations from the official ISERN website
and saves the data as a JSON file for use with other ISERN analysis programs.

Usage:
    python scrape_isern_members.py

Output:
    isern_members.json - Contains member names and their organizations
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time


def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove any remaining HTML entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text


def extract_member_info(member_element):
    """Extract member name and organization from a member element"""
    member_info = {}
    
    # Get the full text content
    full_text = clean_text(member_element.get_text())
    
    # Pattern 1: "Organization (Country), Name"
    if ',' in full_text:
        parts = full_text.split(',', 1)  # Split on first comma only
        if len(parts) == 2:
            org_part = parts[0].strip()
            name_part = parts[1].strip()
            
            # The organization part might have country in parentheses
            # e.g., "Aalto University School of Science and Technology (TKK) (Finland)"
            member_info['organization'] = org_part
            member_info['name'] = name_part
            return member_info
    
    # Pattern 2: Look for strong/bold tags which might contain names
    name_element = member_element.find(['strong', 'b'])
    if name_element:
        potential_name = clean_text(name_element.get_text())
        # Check if this looks like a person's name
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+(\s+[A-Z][a-z]+)*$', potential_name):
            member_info['name'] = potential_name
            # Rest is organization
            org_text = full_text.replace(potential_name, '').strip()
            org_text = re.sub(r'^[,\-–\s]+', '', org_text)
            if org_text:
                member_info['organization'] = org_text
            return member_info
    
    # Pattern 3: Try to identify name vs organization by common patterns
    # Look for university/institute keywords to identify organization
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    if len(lines) >= 2:
        # Multiple lines - try to identify which is name vs org
        for i, line in enumerate(lines):
            # If line contains university/institute keywords, it's likely organization
            if any(keyword in line.lower() for keyword in [
                'university', 'institute', 'college', 'school', 'research',
                'emeritus', 'corporation', 'center', 'centre', 'gmbh', 'ltd'
            ]):
                # This line is likely organization
                member_info['organization'] = line
                # Look for a name in other lines
                for j, other_line in enumerate(lines):
                    if i != j and re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+(\s+[A-Z][a-z]+)*$', other_line.strip()):
                        member_info['name'] = other_line.strip()
                        break
                break
    
    # Pattern 4: Single line with name pattern
    if not member_info and re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+(\s+[A-Z][a-z]+)*$', full_text.strip()):
        member_info['name'] = full_text.strip()
        member_info['organization'] = ''
    
    # Pattern 5: If all else fails and we have some text that contains a name pattern
    if not member_info:
        name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', full_text)
        if name_match:
            potential_name = name_match.group(1)
            member_info['name'] = potential_name
            # Everything else might be organization
            org_text = full_text.replace(potential_name, '').strip()
            org_text = re.sub(r'^[,\-–\s]+', '', org_text)
            if org_text:
                member_info['organization'] = org_text
    
    return member_info


def scrape_isern_members():
    """Scrape ISERN members from the official website"""
    url = "https://isern.iese.de/isern-members-2/"
    
    print(f"Scraping ISERN members from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    members = []
    
    # Debug: Check for specific missing members in the raw content
    missing_members = ['Danilo Caivano', 'Magne Jørgensen', 'Martin Solari', 'Tomi Männistö']
    page_text = soup.get_text()
    
    print("\nChecking for missing members in page content:")
    for member in missing_members:
        if member in page_text:
            print(f"✓ Found '{member}' in page text")
        else:
            print(f"✗ '{member}' not found in page text")
    
    # Look for different possible structures on the page
    # Try to find the main content area
    content_areas = [
        soup.find('div', class_='entry-content'),
        soup.find('div', class_='content'),
        soup.find('main'),
        soup.find('article'),
        soup.find('div', class_='post-content'),
        soup.find('div', class_='page-content'),
        soup
    ]
    
    for content in content_areas:
        if content is None:
            continue
            
        print(f"\nSearching in content area: {content.name if hasattr(content, 'name') else 'root'}")
        
        # Look for lists or structured content
        member_elements = []
        
        # Try different selectors for member listings - be more comprehensive
        selectors = [
            'li',  # List items
            'p',   # Paragraphs  
            'div.member',  # Specific member divs
            'tr',  # Table rows
            'div',  # All divs
            'span',  # Spans that might contain member info
        ]
        
        for selector in selectors:
            elements = content.find_all(selector)
            if elements:
                print(f"  Checking {len(elements)} elements with selector '{selector}'")
                
                for element in elements:
                    text = clean_text(element.get_text())
                    
                    # Skip very short text or common non-member content
                    if len(text) < 5:
                        continue
                    if any(skip_word in text.lower() for skip_word in [
                        'home', 'contact', 'about', 'menu', 'search', 'login', 
                        'copyright', 'privacy', 'cookie', 'navigation', 'toggle',
                        'skip to', 'main content'
                    ]):
                        continue
                    
                    # Check if this text contains any of our missing members
                    for missing in missing_members:
                        if missing.lower() in text.lower():
                            print(f"  🔍 Found missing member '{missing}' in element: {text[:100]}...")
                    
                    # Look for patterns that suggest this is a member entry
                    # Pattern 1: "Organization (Country), Name"
                    if ',' in text and re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', text):
                        member_info = extract_member_info(element)
                        if member_info.get('name') and len(member_info['name']) > 3:
                            print(f"  Found potential member (Pattern 1): {member_info}")
                            members.append(member_info)
                    
                    # Pattern 2: Just a name on its own (might be in a different structure)
                    elif re.search(r'^[A-Z][a-z]+ [A-Z][a-z]+(\s+[A-Z][a-z]+)*\s*$', text.strip()):
                        print(f"  Found potential name-only member: {text.strip()}")
                        member_info = {'name': text.strip(), 'organization': ''}
                        members.append(member_info)
                    
                    # Pattern 3: Look for lines that contain organization keywords
                    elif any(keyword in text.lower() for keyword in [
                        'university', 'institute', 'college', 'school', 'research',
                        'emeritus', 'corporation', 'center', 'centre'
                    ]) and re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', text):
                        member_info = extract_member_info(element)
                        if member_info.get('name') and len(member_info['name']) > 3:
                            print(f"  Found potential member (Pattern 3): {member_info}")
                            members.append(member_info)
                
                # If we found members with this selector, we might want to continue
                # checking other selectors too since the page might have mixed formats
        
        # If we found a good number of members in this content area, we can break
        if len(members) > 50:
            print(f"Found {len(members)} members in this content area")
            break
    
    # Additional fallback: try to parse the entire page more liberally
    if len(members) < 50:
        print(f"\nOnly found {len(members)} members so far. Trying more liberal parsing...")
        
        # Look for any text that mentions the missing members specifically
        all_paragraphs = soup.find_all(['p', 'div', 'li', 'td'])
        
        for para in all_paragraphs:
            text = clean_text(para.get_text())
            
            # Check if this paragraph contains any missing member
            for missing in missing_members:
                if missing.lower() in text.lower():
                    print(f"  Found paragraph with '{missing}': {text}")
                    
                    # Try to extract member info from this specific paragraph
                    member_info = extract_member_info(para)
                    if member_info.get('name'):
                        print(f"    Extracted: {member_info}")
                        members.append(member_info)
    
    # Remove duplicates based on name
    unique_members = []
    seen_names = set()
    
    for member in members:
        name = member.get('name', '').strip()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_members.append(member)
    
    print(f"\nFound {len(unique_members)} unique members")
    
    # Final check: verify we got the missing members
    found_names = {member.get('name', '') for member in unique_members}
    print(f"\nFinal check for missing members:")
    for missing in missing_members:
        if missing in found_names:
            print(f"✓ Successfully scraped: {missing}")
        else:
            print(f"✗ Still missing: {missing}")
    
    return unique_members


def save_members_json(members, filename="isern_members.json"):
    """Save members data to JSON file"""
    if not members:
        print("No members to save")
        return
    
    data = {
        'scraped_date': datetime.now().isoformat(),
        'source_url': 'https://isern.iese.de/isern-members-2/',
        'total_members': len(members),
        'members': members
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(members)} members to {filename}")


def main():
    """Main function"""
    print("ISERN Members Scraper")
    print("=" * 50)
    
    # Add a small delay to be respectful to the server
    time.sleep(1)
    
    # Scrape the members
    members = scrape_isern_members()
    
    if members:
        # Save to JSON
        save_members_json(members)
        
        # Print summary
        print("\nScraping Summary:")
        print(f"Total members found: {len(members)}")
        print("\nFirst 5 members:")
        for i, member in enumerate(members[:5]):
            print(f"  {i+1}. {member.get('name', 'Unknown')} - {member.get('organization', 'No org')}")
        
        if len(members) > 5:
            print(f"  ... and {len(members) - 5} more")
    else:
        print("Failed to scrape any members")
        
        # Let's try to see what the page structure looks like
        print("\nDebugging: Let's examine the page structure...")
        try:
            response = requests.get("https://isern.iese.de/isern-members-2/", timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Print the page title
            title = soup.find('title')
            print(f"Page title: {title.get_text() if title else 'No title found'}")
            
            # Look for any lists
            lists = soup.find_all(['ul', 'ol'])
            print(f"Found {len(lists)} lists on the page")
            
            # Look for any divs with text content
            divs = soup.find_all('div')
            text_divs = [div for div in divs if div.get_text().strip()]
            print(f"Found {len(text_divs)} divs with text content")
            
            # Show some sample content
            content = soup.get_text()[:500]
            print(f"Sample page content:\n{content}...")
            
        except Exception as e:
            print(f"Error during debugging: {e}")


if __name__ == "__main__":
    main()
