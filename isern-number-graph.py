import networkx as nx
import matplotlib.pyplot as plt
import json
import os
import sys

def load_isern_numbers_data():
    """Load ISERN numbers data from JSON file"""
    json_filename = "isern_numbers.json"
    
    if not os.path.exists(json_filename):
        print(f"Error: {json_filename} not found!")
        print("\nThis script requires precomputed ISERN numbers data.")
        print("Please run 'isern-number-dlbp.py' first to generate the required data file.")
        print("That script will:")
        print("  1. Query DBLP for all ISERN member collaborations")
        print("  2. Build the collaboration network")
        print("  3. Calculate ISERN numbers from founding members")
        print("  4. Generate isern_numbers.json for use by this script")
        print("\nAfter running isern-number-dlbp.py, you can use this script for fast visualization.")
        sys.exit(1)
    
    try:
        with open(json_filename, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded ISERN numbers data from {json_filename}")
        return data
    except Exception as e:
        print(f"Error loading {json_filename}: {e}")
        sys.exit(1)

def create_graph_from_data(data):
    """Create a NetworkX graph from the loaded ISERN numbers data"""
    # Create an empty graph
    G = nx.Graph()
    
    # Add all members as nodes with their ISERN numbers
    isern_numbers = data['isern_numbers']
    for member, number in isern_numbers.items():
        # Convert "infinity" back to float('inf')
        isern_num = float('inf') if number == "infinity" else number
        G.add_node(member, isern_number=isern_num, level=int(isern_num) if isern_num != float('inf') else -1)
    
    # Load collaboration edges from the coauthorship graph file
    coauth_filename = "isern_coauthorship_graph.json"
    if os.path.exists(coauth_filename):
        try:
            with open(coauth_filename, 'r') as f:
                coauth_data = json.load(f)
            
            # Add edges from the collaboration data
            if 'edges' in coauth_data:
                edges_added = 0
                for edge in coauth_data['edges']:
                    source = edge['source']
                    target = edge['target']
                    # Only add edge if both nodes exist in our ISERN numbers graph
                    if source in G.nodes() and target in G.nodes():
                        G.add_edge(source, target)
                        edges_added += 1
                
                print(f"Created graph with {G.number_of_nodes()} nodes and {edges_added} collaboration edges")
            else:
                print(f"Created graph with {G.number_of_nodes()} nodes (no edges data found)")
                
        except Exception as e:
            print(f"Warning: Could not load collaboration edges from {coauth_filename}: {e}")
            print(f"Created graph with {G.number_of_nodes()} nodes (no edges)")
    else:
        print(f"Warning: {coauth_filename} not found - visualization will show nodes without collaboration edges")
        print(f"Created graph with {G.number_of_nodes()} nodes (no edges)")
    
    return G, isern_numbers

def create_layered_visualization(G, isern_numbers_dict):
    """Create a layered visualization showing ISERN numbers"""
    # Convert string "infinity" back to float('inf') for processing
    isern_numbers = {}
    for member, number in isern_numbers_dict.items():
        isern_numbers[member] = float('inf') if number == "infinity" else number
    
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
    
    return pos, levels, isern_numbers

def main():
    # Load precomputed ISERN numbers data
    data = load_isern_numbers_data()
    
    # Extract key information
    isern_numbers_dict = data['isern_numbers']
    founding_members = data.get('founding_members', [])
    total_members = data.get('total_members', len(isern_numbers_dict))
    connected_members = data.get('connected_members', 0)
    
    print(f"\nLoaded ISERN Numbers Data:")
    print(f"Total members: {total_members}")
    print(f"Connected members: {connected_members}")
    print(f"Founding members: {founding_members}")
    
    # Create a graph structure for visualization (nodes only, no edges needed)
    G, isern_numbers_for_graph = create_graph_from_data(data)
    
    # Create layered visualization
    pos, levels, isern_numbers = create_layered_visualization(G, isern_numbers_dict)
    
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
    
    # Draw collaboration edges if they exist
    if G.number_of_edges() > 0:
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
    print(f"\nISERN numbers visualization saved: {plot_filename}")
    
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
