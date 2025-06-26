import json
import os

def load_isern_members(filename='isern_members.json'):
    """
    Load ISERN members from JSON file
    
    Args:
        filename (str): Path to the JSON file containing ISERN members
    
    Returns:
        list: List of ISERN member names
    """
    try:
        # Try to find the file in current directory or script directory
        if not os.path.exists(filename):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, filename)
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        members = data['isern_members']
        print(f"Loaded {len(members)} ISERN members from {filename}")
        
        if 'metadata' in data:
            metadata = data['metadata']
            print(f"Last updated: {metadata.get('last_updated', 'Unknown')}")
            print(f"Total members in file: {metadata.get('total_members', len(members))}")
        
        return members
    
    except FileNotFoundError:
        print(f"Error: {filename} file not found!")
        print("Please ensure the file exists in the current directory or script directory.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        return []
    except Exception as e:
        print(f"Error loading ISERN members: {e}")
        return []

def save_isern_members(members, filename='isern_members.json', metadata=None):
    """
    Save ISERN members to JSON file
    
    Args:
        members (list): List of ISERN member names
        filename (str): Path to save the JSON file
        metadata (dict): Optional metadata to include
    """
    try:
        data = {
            "isern_members": members
        }
        
        if metadata:
            data["metadata"] = metadata
        else:
            data["metadata"] = {
                "description": "ISERN (International Software Engineering Research Network) member list",
                "last_updated": "2024-01-01",
                "source": "Official ISERN page",
                "total_members": len(members)
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(members)} ISERN members to {filename}")
        return True
    
    except Exception as e:
        print(f"Error saving ISERN members: {e}")
        return False
