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
                coauthor_norm = normalize(coauthor)
                # Check if this coauthor is also an ISERN member
                for other_member in isern_members:
                    if normalize(other_member) == coauthor_norm and other_member != member:
                        G.add_edge(member, other_member)
                        print(f"  Found collaboration: {member} <-> {other_member}")
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
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
