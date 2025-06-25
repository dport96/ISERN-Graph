import requests
import xmltodict
import networkx as nx
import time
import matplotlib.pyplot as plt
import json
from datetime import datetime
from urllib.parse import quote

# Founding members of ISERN with their organizations and contacts
founding_isern_members = [
    {"organization": "Nara Institute of Science and Technology (Japan)", "contact": "Prof. Dr. Koji Torii"},
    {"organization": "University of Kaiserslautern, FB Informatik, AG Software Engineering (Germany)", "contact": "Prof. Dr. Dieter Rombach"},
    {"organization": "University of Maryland at College Park, Department of Computer Science (USA)", "contact": "Prof. Dr. V.R. Basili"},
    {"organization": "University of New South Wales, Sydney, School of Information Systems (Australia)", "contact": "Prof. Dr. Ross Jeffery"},
    {"organization": "University of Roma at Tor Vergata, Laboratory for Computer Science (Italy)", "contact": "Prof. Dr. Giovanni Cantone"},
    {"organization": "VTT Electronics, Technical Research Centre of Finland", "contact": "Dr. Markku Oivo"}
]


# Full ISERN member list from the official page [1][3]
isern_members = [
    "Caspar Lassenius",
    "Eray Tüzün",
    "Nauman bin Ali",
    "Hakan Erdogmus",
    "Robert Feldt",
    "Guilherme Travassos",
    "Michael Felderer",
    "Markku Oivo",
    "Fabio Q.B. da Silva",
    "Daniel Mendez Fernandez",
    "Andreas Jedlitschka",
    "Barbara Russo",
    "Qing Wang",
    "Per Runeson",
    "Maria Paasivaara",
    "Clemente Izurieta",
    "He Zhang",
    "Kenichi Matsumoto",
    "Jingyu Li",
    "Laurie Williams",
    "Takeshi Hayama",
    "Shinji Kusumoto",
    "Minghui Zhou",
    "Marcos Kalinowski",
    "Rafael Prikladnicki",
    "Marcus Ciolkowski",
    "Desmond Greer",
    "Ayşe Başar",
    "Magne Jørgensen",
    "Nils Brede Moe",
    "Danilo Caivano",
    "Xavier Franch",
    "Ali Babar",
    "Paris Avgeriou",
    "Sira Vegas",
    "Oscar Pastor",
    "Sandro Morasca",
    "Jeffrey Carver",
    "Maria Teresa Baldassarre",
    "Marcela Genero",
    "Dan Port",
    "Tomi Männistö",
    "Rahul Mohanani",
    "Carolyn Seaman",
    "Dag Sjøberg",
    "Burak Turhan",
    "Stefan Wagner",
    "Dietmar Pfahl",
    "Audris Mockus",
    "Maya Daneva",
    "Martin Solari",
    "Maurizio Morisio",
    "Stefan Biffl",
    "Rogardt Heldal",
    "Victor Basili",
    "Giovanni Cantone",
    "Dieter Rombach",
    "Ross Jeffery"
    # Add or adjust names as needed for completeness
]

# Normalize names for matching (e.g., lowercase, strip accents if needed)
def normalize(name):
    return name.lower().replace("ö", "o").replace("ü", "u").replace("ç", "c")  # expand as needed

def names_match(name1, name2):
    """Check if two names likely refer to the same person, handling common variations"""
    if name1 == name2:
        return True
    
    # Normalize both names
    norm1 = normalize(name1)
    norm2 = normalize(name2)
    
    if norm1 == norm2:
        return True
    
    # Split into parts for more flexible matching
    parts1 = norm1.split()
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
    """Search for an author in DBLP using both author search and publication search"""
    try:
        print(f"Searching for {author_name}...")
        
        # First, try to find the author using DBLP's author search API
        author_variations = get_dblp_author_variations(author_name)
        
        # If we found author variations, use them; otherwise fall back to manual variations
        if author_variations:
            print(f"  Found {len(author_variations)} author variations from DBLP")
            variations = author_variations
        else:
            print(f"  No author found in DBLP author search, using manual variations")
            variations = generate_manual_variations(author_name)
        
        best_publications = []
        best_variation = ""
        
        for variation in variations:
            try:
                print(f"  Trying variation: {variation}")
                
                # URL encode the author name
                encoded_name = quote(variation)
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
                
                if len(publications) > len(best_publications):
                    best_publications = publications
                    best_variation = variation
                    print(f"    Found {len(publications)} publications (NEW BEST)")
                    if len(publications) > 50:  # Good enough, stop trying
                        break
                else:
                    print(f"    Found {len(publications)} publications")
                
                time.sleep(0.5)  # Be nice to DBLP servers
                
            except Exception as e:
                print(f"    Error with variation '{variation}': {e}")
                continue
        
        print(f"  Best result: {len(best_publications)} publications using '{best_variation}'")
        return best_publications
        
    except Exception as e:
        print(f"Error searching for {author_name}: {e}")
        return []

def get_dblp_author_variations(author_name):
    """Get author name variations directly from DBLP's author search API"""
    try:
        # Search for the author using DBLP's author search
        encoded_name = quote(author_name)
        url = f"https://dblp.org/search/author/api?q={encoded_name}&format=xml&h=10"
        
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse XML response
        data = xmltodict.parse(response.content)
        
        variations = []
        # The structure is: data['result']['hits']['hit'] (xmltodict wraps the root <r> as 'result')
        if 'result' in data and 'hits' in data['result'] and 'hit' in data['result']['hits']:
            hits = data['result']['hits']['hit']
            
            if not isinstance(hits, list):
                hits = [hits]
            
            for hit in hits:
                if 'info' in hit and 'author' in hit['info']:
                    # Add the main author name
                    main_author = hit['info']['author']
                    if names_match(author_name, main_author):
                        variations.append(main_author)
                    
                    # Add aliases if they exist
                    if 'aliases' in hit['info'] and 'alias' in hit['info']['aliases']:
                        aliases = hit['info']['aliases']['alias']
                        if not isinstance(aliases, list):
                            aliases = [aliases]
                        
                        for alias in aliases:
                            if names_match(author_name, alias):
                                variations.append(alias)
        
        # Remove duplicates
        unique_variations = list(dict.fromkeys(variations))  # Preserves order
        
        return unique_variations
        
    except Exception as e:
        print(f"    Error in DBLP author search: {e}")
        return []

def generate_manual_variations(author_name):
    """Generate manual name variations as fallback"""
    variations = [author_name]
    
    # Add common variations
    name_parts = author_name.split()
    if len(name_parts) >= 2:
        # Try First Last format
        variations.append(f"{name_parts[0]} {name_parts[-1]}")
        # Try Last, First format
        variations.append(f"{name_parts[-1]}, {name_parts[0]}")
        # Try F. Last format
        variations.append(f"{name_parts[0][0]}. {name_parts[-1]}")
    
    # Special cases for known ISERN members
    if "Dan Port" in author_name:
        variations.extend(["Daniel Port", "D. Port"])
    elif "Victor Basili" in author_name:
        variations.extend(["Victor R. Basili", "V.R. Basili", "V. Basili"])
    elif "Guilherme Travassos" in author_name:
        variations.extend(["Guilherme H. Travassos", "G. H. Travassos"])
    elif "Fabio Q.B. da Silva" in author_name:
        variations.extend(["Fábio Q. B. da Silva", "Fabio Queda Bueno da Silva"])
    elif "Daniel Mendez Fernandez" in author_name:
        variations.extend(["Daniel Méndez", "Daniel Mendez", "D. Méndez"])
    
    return variations

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

# Build co-authorship graph
G = nx.Graph()
G.add_nodes_from(isern_members)

print("Building co-authorship graph for ISERN members...")
print("This may take a while as we query DBLP for each member...")

for i, member in enumerate(isern_members, 1):
    print(f"Processing {i}/{len(isern_members)}: {member}")
    try:
        publications = search_dblp_author(member)
        
        for pub in publications:
            coauthors = get_coauthors_from_publication(pub)
            
            for coauthor in coauthors:
                # Check if this coauthor is also an ISERN member using improved matching
                for other_member in isern_members:
                    if names_match(coauthor, other_member) and other_member != member:
                        G.add_edge(member, other_member)
                        print(f"  Found collaboration: {member} <-> {other_member} (via coauthor '{coauthor}')")
                        break
        
        # Be respectful to DBLP API
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error processing {member}: {e}")

# Now G is your co-authorship graph
print(f"\nGraph Statistics:")
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")
print(f"Number of connected components: {nx.number_connected_components(G)}")

# Print edges
print("\nCo-authorship edges between ISERN members:")
for edge in G.edges():
    print(edge)

# Save graph data to files
timestamp = datetime.now().strftime("%Y%m%d")

# Save as GraphML (preserves node/edge attributes and can be read by many tools)
graphml_filename = f"isern_coauthorship_graph_{timestamp}.graphml"
nx.write_graphml(G, graphml_filename)
print(f"\nGraph saved as GraphML: {graphml_filename}")

# Save as JSON (more readable, can be used in web visualizations)
graph_data = {
    "nodes": [{"id": node, "label": node} for node in G.nodes()],
    "edges": [{"source": edge[0], "target": edge[1]} for edge in G.edges()],
    "metadata": {
        "timestamp": timestamp,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "connected_components": nx.number_connected_components(G)
    }
}

json_filename = f"isern_coauthorship_graph_{timestamp}.json"
with open(json_filename, 'w') as f:
    json.dump(graph_data, f, indent=2)
print(f"Graph saved as JSON: {json_filename}")

# Save edge list (simple format)
edgelist_filename = f"isern_coauthorship_edgelist_{timestamp}.txt"
nx.write_edgelist(G, edgelist_filename)
print(f"Graph saved as edge list: {edgelist_filename}")

# Create visualization
plt.figure(figsize=(20, 16))
pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

# Draw the graph
nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                      node_size=1000, alpha=0.8)
nx.draw_networkx_edges(G, pos, edge_color='gray', 
                      alpha=0.6, width=2)
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

plt.title("ISERN Members Co-authorship Network", fontsize=16, fontweight='bold')
plt.axis('off')
plt.tight_layout()

# Save the plot
plot_filename = f"isern_coauthorship_graph_{timestamp}.png"
plt.savefig(plot_filename, dpi=300, bbox_inches='tight', 
           facecolor='white', edgecolor='none')
print(f"Graph visualization saved: {plot_filename}")

# Show the plot
plt.show()

# Print some network analysis
if G.number_of_edges() > 0:
    print("\nNetwork Analysis:")
    print(f"Graph density: {nx.density(G):.4f}")
    
    # Find most connected researchers
    degree_centrality = nx.degree_centrality(G)
    sorted_centrality = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
    
    print("\nTop 10 most connected researchers:")
    for i, (researcher, centrality) in enumerate(sorted_centrality[:10], 1):
        degree = G.degree(researcher)
        print(f"{i:2d}. {researcher}: {degree} collaborations (centrality: {centrality:.4f})")
    
    # Find largest connected component
    largest_cc = max(nx.connected_components(G), key=len)
    print(f"\nLargest connected component has {len(largest_cc)} members:")
    for member in sorted(largest_cc):
        print(f"  - {member}")
else:
    print("\nNo collaborations found in the data.")
    print("This might be due to:")
    print("- Name variations in DBLP (different spellings, initials, etc.)")
    print("- Limited API results")
    print("- Authors publishing under different name formats")
