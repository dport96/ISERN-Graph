#!/usr/bin/env python3
"""
Full ISERN Member Collaboration Network Discovery
Optimized version for processing all ISERN members efficiently
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
from collections import defaultdict, Counter
import sys
import os
import networkx as nx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_name_utils import EnhancedNameMatcher

def search_dblp_for_author_optimized(author_name, max_hits=150):
    """
    Optimized DBLP search - fewer variants, smaller hit count for efficiency
    """
    print(f"🔍 {author_name}")
    
    # Use fewer, more targeted search variants
    name_parts = author_name.split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        search_variants = [
            f'author:"{author_name}"',  # Full name (exact)
            f'"{last_name}" "{first_name}"',  # General search
        ]
        
        # Only add initial variant if it's likely to be effective
        if len(first_name) > 1:
            search_variants.append(f'author:"{first_name[0]}. {last_name}"')
    else:
        search_variants = [f'author:"{author_name}"']
    
    all_publications = []
    
    for variant in search_variants:
        try:
            response = requests.get(
                "https://dblp.org/search/publ/api",
                params={'q': variant, 'format': 'xml', 'h': max_hits},
                timeout=20
            )
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                for hit in root.findall('.//hit'):
                    info = hit.find('info')
                    if info is not None:
                        # Extract authors only (minimal data for efficiency)
                        authors = []
                        for author in info.findall('authors/author'):
                            if author.text:
                                authors.append(author.text.strip())
                        
                        if authors:  # Only keep if we have authors
                            title_elem = info.find('title')
                            title = title_elem.text if title_elem is not None else "No title"
                            
                            all_publications.append({
                                'title': title,
                                'authors': authors
                            })
                        
        except Exception as e:
            print(f"   Error: {e}")
            continue
        
        time.sleep(0.2)  # Shorter delay
    
    # Deduplicate by title
    unique_publications = {}
    for pub in all_publications:
        title_key = pub['title'].lower().strip()
        if title_key not in unique_publications:
            unique_publications[title_key] = pub
    
    final_pubs = list(unique_publications.values())
    print(f"   📚 {len(final_pubs)} pubs, ", end="")
    
    return final_pubs

def find_all_isern_collaborations(isern_members):
    """Find collaborations between all ISERN members efficiently"""
    
    print(f"🚀 FULL ISERN COLLABORATION NETWORK DISCOVERY")
    print(f"=" * 60)
    print(f"📋 Processing all {len(isern_members)} ISERN members")
    print(f"⏱️  Estimated time: ~{len(isern_members) * 15} seconds ({len(isern_members) * 15 // 60} minutes)")
    
    # Initialize name matcher
    name_matcher = EnhancedNameMatcher(similarity_threshold=0.85)
    
    # Track collaborations
    collaborations = defaultdict(set)
    collaboration_counts = defaultdict(int)
    
    # Process each member
    start_time = time.time()
    
    for i, member in enumerate(isern_members, 1):
        print(f"\n{i:2d}/{len(isern_members)} ", end="")
        
        # Get publications
        publications = search_dblp_for_author_optimized(member)
        
        if not publications:
            print("❌ No publications")
            continue
        
        # Extract coauthors
        all_coauthors = set()
        for pub in publications:
            for author in pub['authors']:
                if author.strip() and author.strip() != member:
                    all_coauthors.add(author.strip())
        
        # Match against ISERN members
        isern_collaborators = []
        for coauthor in all_coauthors:
            matches = name_matcher.find_best_matches(coauthor, isern_members, top_k=1)
            if matches:
                best_match, score, _ = matches[0]
                if score >= 0.85 and best_match != member:
                    isern_collaborators.append(best_match)
        
        # Record collaborations
        unique_collaborators = set(isern_collaborators)
        for collaborator in unique_collaborators:
            collaborations[member].add(collaborator)
            collaborations[collaborator].add(member)
            collaboration_counts[f"{min(member, collaborator)}|{max(member, collaborator)}"] += 1
        
        print(f"👥 {len(unique_collaborators)} ISERN collabs")
        
        # Progress update every 10 members
        if i % 10 == 0:
            elapsed = time.time() - start_time
            remaining = (elapsed / i) * (len(isern_members) - i)
            total_edges = len(collaboration_counts)
            print(f"   📊 Progress: {total_edges} collaborations found, ~{remaining/60:.1f}min remaining")
    
    return collaborations, collaboration_counts

def create_enhanced_network_analysis(collaborations, isern_members):
    """Create comprehensive network analysis"""
    
    print(f"\n📊 COMPREHENSIVE NETWORK ANALYSIS")
    print(f"=" * 40)
    
    # Create graph
    G = nx.Graph()
    G.add_nodes_from(isern_members)
    
    # Add edges
    for member, collaborators in collaborations.items():
        for collaborator in collaborators:
            if not G.has_edge(member, collaborator):
                G.add_edge(member, collaborator)
    
    print(f"🌐 Network Overview:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    print(f"   Density: {nx.density(G):.3f}")
    print(f"   Connected components: {nx.number_connected_components(G)}")
    
    # Connected components analysis
    components = list(nx.connected_components(G))
    components.sort(key=len, reverse=True)
    
    print(f"\n🏢 Connected Components:")
    for i, component in enumerate(components[:5], 1):
        print(f"   {i}. {len(component)} members")
        if len(component) <= 5:
            print(f"      {', '.join(sorted(component))}")
    
    if len(components) > 5:
        print(f"   ... and {len(components) - 5} smaller components")
    
    # Central nodes analysis
    if G.number_of_edges() > 0:
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        print(f"\n🏆 Most Connected Members (Top 10):")
        top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        for member, centrality in top_degree:
            degree = G.degree(member)
            if degree > 0:
                print(f"   {member}: {degree} collaborations")
        
        print(f"\n🌉 Key Bridge Connectors (Top 5):")
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        for member, centrality in top_betweenness:
            if centrality > 0:
                print(f"   {member}: {centrality:.3f}")
        
        # Network insights
        print(f"\n🔍 Network Insights:")
        isolated = [n for n in G.nodes() if G.degree(n) == 0]
        print(f"   Isolated members: {len(isolated)}")
        if len(isolated) <= 10:
            print(f"   {', '.join(sorted(isolated))}")
        
        connected_members = [n for n in G.nodes() if G.degree(n) > 0]
        print(f"   Connected members: {len(connected_members)}")
        
        if len(components) > 0:
            largest_component = components[0]
            print(f"   Largest component: {len(largest_component)} members ({len(largest_component)/len(isern_members)*100:.1f}%)")
    
    return G

def save_comprehensive_results(collaborations, G, isern_members):
    """Save comprehensive results in multiple formats"""
    
    print(f"\n💾 SAVING COMPREHENSIVE RESULTS")
    print(f"=" * 35)
    
    # Summary statistics
    stats = {
        'total_members': len(isern_members),
        'total_collaborations': G.number_of_edges(),
        'network_density': nx.density(G),
        'connected_components': nx.number_connected_components(G),
        'connected_members': len([n for n in G.nodes() if G.degree(n) > 0]),
        'isolated_members': len([n for n in G.nodes() if G.degree(n) == 0]),
        'largest_component_size': len(max(nx.connected_components(G), key=len)) if G.number_of_edges() > 0 else 0
    }
    
    # Member-level data
    member_data = {}
    for member in isern_members:
        member_data[member] = {
            'collaboration_count': len(collaborations.get(member, set())),
            'collaborators': sorted(list(collaborations.get(member, set()))),
            'degree_centrality': nx.degree_centrality(G).get(member, 0),
            'betweenness_centrality': nx.betweenness_centrality(G).get(member, 0) if G.number_of_edges() > 0 else 0,
            'closeness_centrality': nx.closeness_centrality(G).get(member, 0) if G.number_of_edges() > 0 else 0
        }
    
    # Complete results
    results = {
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'full_member_to_member_collaboration_discovery',
            'description': 'Complete ISERN collaboration network from DBLP data'
        },
        'network_statistics': stats,
        'members': member_data
    }
    
    # Save main results file
    with open('isern_full_collaboration_network.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"📄 Main results: isern_full_collaboration_network.json")
    
    # Save GraphML for network analysis tools
    nx.write_graphml(G, 'isern_full_collaboration_network.graphml')
    print(f"🌐 Network graph: isern_full_collaboration_network.graphml")
    
    # Save simple edge list
    with open('isern_full_collaboration_edgelist.txt', 'w', encoding='utf-8') as f:
        f.write("Member1\tMember2\n")
        for edge in G.edges():
            f.write(f"{edge[0]}\t{edge[1]}\n")
    print(f"📋 Edge list: isern_full_collaboration_edgelist.txt")
    
    # Save collaboration summary
    with open('isern_collaboration_summary.txt', 'w', encoding='utf-8') as f:
        f.write("ISERN Collaboration Network Summary\n")
        f.write("===================================\n\n")
        f.write(f"Total Members: {stats['total_members']}\n")
        f.write(f"Total Collaborations: {stats['total_collaborations']}\n")
        f.write(f"Network Density: {stats['network_density']:.3f}\n")
        f.write(f"Connected Members: {stats['connected_members']}\n")
        f.write(f"Isolated Members: {stats['isolated_members']}\n\n")
        
        f.write("Top Collaborators:\n")
        top_collaborators = sorted(member_data.items(), key=lambda x: x[1]['collaboration_count'], reverse=True)
        for member, data in top_collaborators[:20]:
            if data['collaboration_count'] > 0:
                f.write(f"  {member}: {data['collaboration_count']} collaborations\n")
    
    print(f"📄 Summary: isern_collaboration_summary.txt")
    
    return results

def main():
    print("🌐 FULL ISERN COLLABORATION NETWORK DISCOVERY")
    print("=" * 50)
    
    # Load ISERN members
    with open('isern_members_enhanced.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        isern_members = data['isern_members']
    
    # Start the full analysis
    collaborations, collaboration_counts = find_all_isern_collaborations(isern_members)
    
    # Analyze the network
    G = create_enhanced_network_analysis(collaborations, isern_members)
    
    # Save comprehensive results
    results = save_comprehensive_results(collaborations, G, isern_members)
    
    # Final summary
    print(f"\n✅ FULL COLLABORATION NETWORK COMPLETE!")
    print(f"   Members processed: {len(isern_members)}")
    print(f"   Collaborations found: {G.number_of_edges()}")
    print(f"   Connected members: {len([n for n in G.nodes() if G.degree(n) > 0])}")
    print(f"   Network density: {nx.density(G):.3f}")
    
    # Check if Dan Port is connected
    dan_port_collabs = len(collaborations.get('Dan Port', set()))
    print(f"\n🎯 Dan Port collaborations: {dan_port_collabs}")
    if dan_port_collabs > 0:
        print(f"   Collaborators: {', '.join(sorted(collaborations['Dan Port']))}")

if __name__ == "__main__":
    main()
