import requests
import xmltodict
import networkx as nx
import time
import matplotlib.pyplot as plt
import json
import os
from urllib.parse import quote
from collections import deque
from enhanced_name_utils import EnhancedNameMatcher
from isern_utils import load_isern_members

# Initialize enhanced name matcher
name_matcher = EnhancedNameMatcher(similarity_threshold=0.85)

# Load ISERN members from JSON file
isern_members = load_isern_members('isern_members_enhanced.json')

# ISERN founding members (Level 0) - extracted from historical records
founding_members = [
    "Koji Torii",           # Nara Institute of Science and Technology (Japan)
    "Dieter Rombach",       # University of Kaiserslautern (Germany) 
    "Victor Basili",        # University of Maryland (USA)
    "Ross Jeffery",         # University of New South Wales (Australia)
    "Giovanni Cantone",     # University of Roma Tor Vergata (Italy)
    "Markku Oivo"          # VTT Electronics (Finland)
]

def is_isern_member(author_name):
    """Check if an author is an ISERN member using enhanced name matching"""
    if not author_name:
        return False
    
    # Use enhanced name matching to find potential ISERN members
    matches = name_matcher.find_best_matches(author_name, isern_members, top_k=1)
    
    if matches and matches[0][1] >= name_matcher.similarity_threshold:
        matched_name = matches[0][0]
        score = matches[0][1]
        print(f"    ISERN member match: {author_name} -> {matched_name} (score: {score:.3f})")
        return True
    
    return False
    parts2 = norm2.split()
    
    if len(parts1) < 2 or len(parts2) < 2:
        return False
    
    # Get first and last names
    first1, last1 = parts1[0], parts1[-1]
    first2, last2 = parts2[0], parts2[-1]
    
    # Last names must match
    if last1 != last2:
        return False
    
    # Check first name variations
    # Full match (Daniel = Daniel)
    if first1 == first2:
        return True
    
    # Initial match (D. = Daniel or Dan)
    if (len(first1) == 2 and first1.endswith('.') and first1[0] == first2[0]) or \
       (len(first2) == 2 and first2.endswith('.') and first2[0] == first1[0]):
        return True
    
    # Common nickname variations
    nickname_map = {
        'daniel': ['dan', 'danny'],
        'dan': ['daniel', 'danny'],
        'william': ['bill', 'will'],
        'bill': ['william'],
        'robert': ['bob', 'rob'],
        'bob': ['robert'],
        'richard': ['rick', 'dick'],
        'rick': ['richard'],
        'michael': ['mike'],
        'mike': ['michael'],
        'christopher': ['chris'],
        'chris': ['christopher'],
        'anthony': ['tony'],
        'tony': ['anthony'],
        'victor': ['vic'],
        'vic': ['victor']
    }
    
    if first1 in nickname_map and first2 in nickname_map[first1]:
        return True
    if first2 in nickname_map and first1 in nickname_map[first2]:
        return True
    
    return False

def search_dblp_author(author_name):
    """Search for an author in DBLP and return their publications"""
    try:
        # URL encode the author name
        encoded_name = quote(author_name)
        url = f"https://dblp.org/search/publ/api?q=author:{encoded_name}&format=xml&h=1000"
        
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse XML response
        data = xmltodict.parse(response.content)
        
        publications = []
        if 'result' in data and 'hits' in data['result'] and 'hit' in data['result']['hits']:
            hits = data['result']['hits']['hit']
            # Handle both single hit and multiple hits
            if isinstance(hits, list):
                for hit in hits:
                    if 'info' in hit:
                        publications.append(hit['info'])
            else:
                if 'info' in hits:
                    publications.append(hits['info'])
        
        return publications
    except Exception as e:
        print(f"Error searching for {author_name}: {e}")
        return []

def get_coauthors_from_publication(pub):
    """Extract coauthor names from a publication"""
    coauthors = []
    try:
        if 'authors' in pub and 'author' in pub['authors']:
            authors = pub['authors']['author']
            if isinstance(authors, list):
                coauthors = [author.get('#text', author) if isinstance(author, dict) else str(author) for author in authors]
            else:
                coauthors = [authors.get('#text', authors) if isinstance(authors, dict) else str(authors)]
    except Exception as e:
        print(f"Error extracting coauthors: {e}")
    return coauthors

def clean_old_cache_files():
    """Remove old cache files - simplified version without timestamps"""
    cache_pattern = "isern_collaboration_cache"
    
    try:
        files_in_dir = os.listdir('.')
        old_cache_files = [f for f in files_in_dir if f.startswith(cache_pattern) and f.endswith('.graphml')]
        
        for old_file in old_cache_files:
            try:
                os.remove(old_file)
                print(f"Removed old cache file: {old_file}")
            except Exception as e:
                print(f"Could not remove {old_file}: {e}")
                
        if not old_cache_files:
            print("No old cache files to clean up")
            
    except Exception as e:
        print(f"Error during cache cleanup: {e}")

def build_collaboration_graph():
    """Build the full collaboration graph between ISERN members"""
    # Check if cached data exists
    cache_filename = "isern_collaboration_cache.graphml"
    
    if os.path.exists(cache_filename):
        print("Found cached collaboration graph")
        print(f"Loading from: {cache_filename}")
        try:
            G = nx.read_graphml(cache_filename)
            print(f"Successfully loaded cached graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            return G
        except Exception as e:
            print(f"Error loading cached graph: {e}")
            print("Falling back to fetching fresh data...")
    
    print("No cached data found for today - fetching fresh collaboration data...")
    G = nx.Graph()
    G.add_nodes_from(isern_members)
    
    print("Building collaboration graph...")
    print("This may take a while as we query DBLP for each member...")
    
    for i, member in enumerate(isern_members, 1):
        print(f"Processing {i}/{len(isern_members)}: {member}")
        try:
            publications = search_dblp_author(member)
            
            for pub in publications:
                coauthors = get_coauthors_from_publication(pub)
                
                for coauthor in coauthors:
                    # Check if this coauthor is also an ISERN member using enhanced matching
                    if is_isern_member(coauthor):
                        # Find the best matching ISERN member name
                        matches = name_matcher.find_best_matches(coauthor, isern_members, top_k=1)
                        if matches:
                            other_member = matches[0][0]
                            if other_member != member:
                                G.add_edge(member, other_member)
                                break
            
            # Be respectful to DBLP API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {member}: {e}")
    
    # Save the graph to cache for future use
    try:
        nx.write_graphml(G, cache_filename)
        print(f"\nCached collaboration graph saved to: {cache_filename}")
    except Exception as e:
        print(f"Warning: Could not save cache file: {e}")
    
    return G

def calculate_isern_numbers(G):
    """Calculate ISERN numbers using BFS from founding members"""
    isern_numbers = {}
    
    # Initialize founding members at level 0
    for founder in founding_members:
        if founder in G.nodes():
            isern_numbers[founder] = 0
    
    print(f"\nFounding members (Level 0): {[f for f in founding_members if f in G.nodes()]}")
    
    # Use BFS to calculate distances
    queue = deque([(founder, 0) for founder in founding_members if founder in G.nodes()])
    visited = set(founding_members)
    
    while queue:
        current_member, current_level = queue.popleft()
        
        # Check all neighbors
        for neighbor in G.neighbors(current_member):
            if neighbor not in visited:
                isern_numbers[neighbor] = current_level + 1
                visited.add(neighbor)
                queue.append((neighbor, current_level + 1))
    
    # Handle disconnected members
    for member in G.nodes():
        if member not in isern_numbers:
            isern_numbers[member] = float('inf')  # Infinite ISERN number
    
    return isern_numbers

def create_layered_visualization(G, isern_numbers):
    """Create a layered visualization showing ISERN numbers"""
    # Group nodes by their ISERN number
    levels = {}
    for member, number in isern_numbers.items():
        if number not in levels:
            levels[number] = []
        levels[number].append(member)
    
    # Create positions for layered layout
    pos = {}
    max_level = max([level for level in levels.keys() if level != float('inf')])
    
    for level, members in levels.items():
        if level == float('inf'):
            level_y = -1  # Place disconnected nodes at the bottom
            level_name = "Disconnected"
        else:
            level_y = max_level - level  # Founders at top
            level_name = f"Level {int(level)}"
        
        print(f"\n{level_name}: {len(members)} members")
        for i, member in enumerate(sorted(members)):
            pos[member] = (i - len(members)/2, level_y)
            if level != float('inf'):
                print(f"  - {member} (ISERN number: {int(level)})")
            else:
                print(f"  - {member} (ISERN number: ∞)")
    
    return pos, levels

def main():
    # Clean up old cache files
    clean_old_cache_files()
    
    # Build collaboration graph (will use cache if available)
    G = build_collaboration_graph()
    
    print(f"\nCollaboration Graph Statistics:")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Number of connected components: {nx.number_connected_components(G)}")
    
    # Calculate ISERN numbers
    isern_numbers = calculate_isern_numbers(G)
    
    # Create layered visualization
    pos, levels = create_layered_visualization(G, isern_numbers)
    
    # Save data
    
    # Save ISERN numbers as JSON
    isern_data = {
        "isern_numbers": {member: (int(num) if num != float('inf') else "infinity") 
                         for member, num in isern_numbers.items()},
        "levels": {str(level): members for level, members in levels.items()},
        "founding_members": founding_members,
        "total_members": len(isern_members),
        "connected_members": len([n for n in isern_numbers.values() if n != float('inf')])
    }
    
    json_filename = "isern_numbers.json"
    with open(json_filename, 'w') as f:
        json.dump(isern_data, f, indent=2)
    print(f"\nISERN numbers saved as JSON: {json_filename}")
    
    # Save graph data
    graphml_filename = "isern_numbers_graph.graphml"
    # Add ISERN numbers as node attributes
    for node in G.nodes():
        G.nodes[node]['isern_number'] = isern_numbers[node]
        G.nodes[node]['level'] = int(isern_numbers[node]) if isern_numbers[node] != float('inf') else -1
    
    nx.write_graphml(G, graphml_filename)
    print(f"Graph with ISERN numbers saved as GraphML: {graphml_filename}")
    
    # Create visualization
    plt.figure(figsize=(24, 16))
    
    # Define darker colors for better contrast with light text
    colors = ['#8B0000', '#FF4500', '#DAA520', '#228B22', '#4169E1', '#8B008B', '#DC143C', '#8B4513']
    node_colors = []
    node_sizes = []
    text_colors = []
    
    for member in G.nodes():
        level = isern_numbers[member]
        if level == float('inf'):
            node_colors.append('#404040')  # Dark gray
            node_sizes.append(600)  # Larger minimum size
            text_colors.append('white')
        else:
            level_int = int(level)
            if level_int < len(colors):
                node_colors.append(colors[level_int])
            else:
                node_colors.append('#708090')  # Slate gray
            # All nodes get larger sizes for better text readability
            node_sizes.append(2000 if level == 0 else 1200)
            text_colors.append('white')
    
    # Draw the graph with improved readability
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                          node_size=node_sizes, alpha=1.0)
    nx.draw_networkx_edges(G, pos, edge_color='gray', 
                          alpha=0.3, width=1)
    
    # Draw labels with better formatting and contrast
    for node, (x, y) in pos.items():
        # Split long names for better fit
        name_parts = node.split()
        if len(name_parts) > 2:
            # For names with more than 2 parts, use first name + last name
            display_name = f"{name_parts[0]}\n{name_parts[-1]}"
        elif len(name_parts) == 2:
            display_name = f"{name_parts[0]}\n{name_parts[1]}"
        else:
            display_name = node
        
        # Determine font size based on node size
        level = isern_numbers[node]
        font_size = 9 if level == 0 else 7
        
        plt.text(x, y, display_name, fontsize=font_size, fontweight='bold',
                ha='center', va='center', color='white',
                bbox=dict(boxstyle="round,pad=0.1", facecolor='black', alpha=0.7))
    
    # Add legend
    legend_elements = []
    for level in sorted([l for l in levels.keys() if l != float('inf')]):
        level_int = int(level)
        if level_int < len(colors):
            color = colors[level_int]
        else:
            color = 'lightgray'
        legend_elements.append(plt.scatter([], [], c=color, s=100, label=f'Level {level_int}'))
    
    if float('inf') in levels:
        legend_elements.append(plt.scatter([], [], c='gray', s=100, label='Disconnected'))
    
    plt.legend(handles=legend_elements, loc='upper right')
    plt.title("ISERN Number Graph\n(Distance from Founding Members)", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Save the plot
    plot_filename = "isern_numbers_graph.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    print(f"ISERN numbers visualization saved: {plot_filename}")
    
    # Show the plot
    plt.show()
    
    # Print summary statistics
    finite_numbers = [num for num in isern_numbers.values() if num != float('inf')]
    if finite_numbers:
        print(f"\nISERN Number Statistics:")
        print(f"Connected members: {len(finite_numbers)}")
        print(f"Disconnected members: {len(isern_numbers) - len(finite_numbers)}")
        print(f"Maximum ISERN number: {max(finite_numbers)}")
        print(f"Average ISERN number: {sum(finite_numbers)/len(finite_numbers):.2f}")
        
        # Distribution by level
        print(f"\nDistribution by level:")
        for level in sorted(levels.keys()):
            if level != float('inf'):
                print(f"  Level {int(level)}: {len(levels[level])} members")
            else:
                print(f"  Disconnected: {len(levels[level])} members")

if __name__ == "__main__":
    main()
