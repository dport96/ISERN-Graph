#!/usr/bin/env python3
"""
Enhanced ISERN Graph Generation using Member-to-Member Collaboration Discovery
This script uses the improved methodology to build the ISERN collaboration graph.
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import time
from collections import defaultdict
import os

def load_collaboration_network():
    """Load the collaboration network from the full discovery results"""
    try:
        with open('isern_full_collaboration_network.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("❌ Full collaboration network file not found.")
        print("   Please run 'python full_isern_collaboration_discovery.py' first.")
        return None

def create_enhanced_isern_graph():
    """Create enhanced ISERN collaboration graph"""
    
    print("🎨 CREATING ENHANCED ISERN COLLABORATION GRAPH")
    print("=" * 50)
    
    # Load collaboration data
    collab_data = load_collaboration_network()
    if not collab_data:
        return None
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes with attributes
    members = collab_data['members']
    for member, data in members.items():
        G.add_node(member, 
                  collaboration_count=data['collaboration_count'],
                  degree_centrality=data['degree_centrality'],
                  betweenness_centrality=data['betweenness_centrality'])
    
    # Add edges
    for member, data in members.items():
        for collaborator in data['collaborators']:
            if not G.has_edge(member, collaborator):
                G.add_edge(member, collaborator)
    
    print(f"📊 Graph created:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    print(f"   Density: {nx.density(G):.3f}")
    
    return G, collab_data

def create_isern_numbers_from_collaboration_graph(G, collab_data):
    """Calculate ISERN numbers from the collaboration graph"""
    
    print(f"\n🔢 CALCULATING ISERN NUMBERS FROM COLLABORATION GRAPH")
    print(f"=" * 55)
    
    # ISERN founders (degree 0)
    founders = [
        "Victor Basili",
        "Dieter Rombach", 
        "Ross Jeffery",
        "Giovanni Cantone",
        "Markku Oivo",
        "Koji Torii"
    ]
    
    isern_numbers = {}
    
    # Set founders to 0
    for founder in founders:
        if founder in G.nodes():
            isern_numbers[founder] = 0
            print(f"   {founder}: ISERN 0 (founder)")
    
    # Use BFS to assign ISERN numbers
    queue = [(founder, 0) for founder in founders if founder in G.nodes()]
    visited = set(founders)
    
    while queue:
        current_member, current_level = queue.pop(0)
        
        # Get neighbors (collaborators)
        for neighbor in G.neighbors(current_member):
            if neighbor not in visited:
                visited.add(neighbor)
                isern_numbers[neighbor] = current_level + 1
                queue.append((neighbor, current_level + 1))
                print(f"   {neighbor}: ISERN {current_level + 1} (via {current_member})")
    
    # Handle any unconnected members
    for member in G.nodes():
        if member not in isern_numbers:
            isern_numbers[member] = 99  # Unconnected
            print(f"   {member}: ISERN 99 (unconnected)")
    
    return isern_numbers

def visualize_enhanced_graph(G, isern_numbers, collab_data):
    """Create enhanced visualization of the ISERN collaboration graph"""
    
    print(f"\n🎨 CREATING ENHANCED VISUALIZATION")
    print(f"=" * 35)
    
    plt.figure(figsize=(20, 16))
    
    # Create layout
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    
    # Color nodes by ISERN number
    color_map = {
        0: '#FF4444',    # Red for founders
        1: '#4444FF',    # Blue for direct collaborators
        2: '#44FF44',    # Green for second-degree
        3: '#FFFF44',    # Yellow for third-degree
        99: '#CCCCCC'    # Gray for unconnected
    }
    
    node_colors = [color_map.get(isern_numbers.get(node, 99), '#CCCCCC') for node in G.nodes()]
    
    # Size nodes by collaboration count
    node_sizes = [collab_data['members'][node]['collaboration_count'] * 100 + 200 
                  for node in G.nodes()]
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, 
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.8)
    
    nx.draw_networkx_edges(G, pos, 
                          alpha=0.3, 
                          width=0.5)
    
    # Add labels for highly connected nodes
    high_degree_nodes = {node: node for node in G.nodes() 
                        if collab_data['members'][node]['collaboration_count'] >= 15}
    
    nx.draw_networkx_labels(G, pos, 
                           labels=high_degree_nodes,
                           font_size=8,
                           font_weight='bold')
    
    # Create legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4444', 
                  markersize=10, label='ISERN 0 (Founders)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4444FF', 
                  markersize=10, label='ISERN 1 (Direct)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#44FF44', 
                  markersize=10, label='ISERN 2 (Second-degree)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFFF44', 
                  markersize=10, label='ISERN 3+ (Higher-degree)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#CCCCCC', 
                  markersize=10, label='Unconnected')
    ]
    
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title('Enhanced ISERN Collaboration Network\n(Node size = collaboration count)', 
              fontsize=16, fontweight='bold')
    plt.axis('off')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('isern_enhanced_collaboration_graph.png', dpi=300, bbox_inches='tight')
    plt.savefig('isern_enhanced_collaboration_graph.pdf', bbox_inches='tight')
    print(f"📊 Graph saved: isern_enhanced_collaboration_graph.png/pdf")
    
    plt.show()

def save_enhanced_results(G, isern_numbers, collab_data):
    """Save enhanced results to multiple formats"""
    
    print(f"\n💾 SAVING ENHANCED RESULTS")
    print(f"=" * 30)
    
    # Update ISERN numbers
    isern_numbers_data = {
        'isern_numbers': isern_numbers,
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'collaboration_graph_based_calculation',
            'total_members': len(isern_numbers),
            'total_collaborations': G.number_of_edges(),
            'network_density': nx.density(G)
        }
    }
    
    with open('isern_numbers_from_collaboration_graph.json', 'w', encoding='utf-8') as f:
        json.dump(isern_numbers_data, f, indent=2, ensure_ascii=False)
    print(f"📄 ISERN numbers: isern_numbers_from_collaboration_graph.json")
    
    # Save GraphML with all attributes
    for node in G.nodes():
        G.nodes[node]['isern_number'] = isern_numbers.get(node, 99)
        member_data = collab_data['members'].get(node, {})
        G.nodes[node]['collaboration_count'] = member_data.get('collaboration_count', 0)
        G.nodes[node]['degree_centrality'] = member_data.get('degree_centrality', 0)
        G.nodes[node]['betweenness_centrality'] = member_data.get('betweenness_centrality', 0)
    
    nx.write_graphml(G, 'isern_enhanced_collaboration_graph.graphml')
    print(f"🌐 Enhanced GraphML: isern_enhanced_collaboration_graph.graphml")
    
    # Summary statistics by ISERN number
    level_counts = defaultdict(int)
    for level in isern_numbers.values():
        level_counts[level] += 1
    
    print(f"\n📈 ISERN Number Distribution:")
    for level in sorted(level_counts.keys()):
        print(f"   ISERN {level}: {level_counts[level]} members")
    
    # Check Dan Port specifically
    dan_port_number = isern_numbers.get('Dan Port', 'Not found')
    print(f"\n🎯 Dan Port's ISERN number: {dan_port_number}")
    if 'Dan Port' in collab_data['members']:
        dan_collabs = collab_data['members']['Dan Port']['collaborators']
        print(f"   Dan Port's collaborators: {', '.join(dan_collabs)}")

def main():
    print("🚀 ENHANCED ISERN GRAPH GENERATION")
    print("=" * 40)
    
    # Create the enhanced graph
    result = create_enhanced_isern_graph()
    if not result:
        return
    
    G, collab_data = result
    
    # Calculate ISERN numbers from the collaboration graph
    isern_numbers = create_isern_numbers_from_collaboration_graph(G, collab_data)
    
    # Create visualization
    visualize_enhanced_graph(G, isern_numbers, collab_data)
    
    # Save results
    save_enhanced_results(G, isern_numbers, collab_data)
    
    print(f"\n✅ ENHANCED ISERN GRAPH COMPLETE!")
    print(f"   Total members: {G.number_of_nodes()}")
    print(f"   Total collaborations: {G.number_of_edges()}")
    print(f"   Network density: {nx.density(G):.3f}")

if __name__ == "__main__":
    main()
