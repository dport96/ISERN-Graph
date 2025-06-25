import networkx as nx
import time
import matplotlib.pyplot as plt
import json
import os
import glob
from datetime import datetime
from scholarly import scholarly, ProxyGenerator
import random
from urllib.parse import unquote

# Full ISERN member list from the official page
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
    "Maya Daneva",
    "Maurizio Morisio",
    "Stefan Biffl",
    "Rogardt Heldal",
    "Victor Basili",
    "Giovanni Cantone",
    "Dieter Rombach",
    "Ross Jeffery",
    "Audris Mockus",
    "Martin Solari"
]

# ISERN founding members (for ISERN number calculation)
founding_members = [
    "Victor Basili",
    "Dieter Rombach", 
    "Giovanni Cantone",
    "Ross Jeffery",
    "Markku Oivo"
]

def setup_proxy():
    """Setup proxy for Google Scholar to avoid rate limiting"""
    try:
        pg = ProxyGenerator()
        success = pg.FreeProxies()
        if success:
            scholarly.use_proxy(pg)
            print("Proxy setup successful")
        else:
            print("Warning: Could not setup proxy, using direct connection")
    except Exception as e:
        print(f"Warning: Proxy setup failed: {e}, using direct connection")

def get_author_publications(author_name, max_results=50):
    """Get publications for an author from Google Scholar"""
    try:
        print(f"Searching for {author_name}...")
        
        # Search for the author
        search_query = scholarly.search_author(author_name)
        author = next(search_query, None)
        
        if not author:
            print(f"  No author found for {author_name}")
            return []
        
        # Fill author details to get publications
        author = scholarly.fill(author, sections=['publications'])
        
        publications = []
        for i, pub in enumerate(author.get('publications', [])):
            if i >= max_results:
                break
                
            try:
                # Fill publication details to get coauthors
                pub_filled = scholarly.fill(pub)
                
                title = pub_filled.get('title', '')
                authors = pub_filled.get('author', '')
                year = pub_filled.get('year', '')
                
                if authors and title:
                    # Parse authors string - Google Scholar returns comma-separated authors
                    author_list = [author.strip() for author in authors.split(',')]
                    
                    publications.append({
                        'title': title,
                        'authors': author_list,
                        'year': year
                    })
                    
            except Exception as e:
                print(f"    Error processing publication {i}: {e}")
                continue
                
        print(f"  Found {len(publications)} publications")
        time.sleep(random.uniform(1, 3))  # Random delay to avoid rate limiting
        return publications
        
    except Exception as e:
        print(f"  Error fetching publications for {author_name}: {e}")
        return []

def extract_coauthors_from_publications(publications, target_members):
    """Extract coauthors who are ISERN members from publications"""
    coauthors = set()
    
    for pub in publications:
        authors = pub.get('authors', [])
        for author in authors:
            # Clean author name
            author_clean = author.strip()
            
            # Check if this author is an ISERN member
            for member in target_members:
                if is_same_author(author_clean, member):
                    coauthors.add(member)
    
    return list(coauthors)

def is_same_author(name1, name2):
    """Check if two author names refer to the same person"""
    # Simple name matching - can be improved with fuzzy matching
    name1_parts = set(name1.lower().split())
    name2_parts = set(name2.lower().split())
    
    # Check if most parts match (handling middle names, initials, etc.)
    if len(name1_parts) >= 2 and len(name2_parts) >= 2:
        # Check if last names match
        if name1_parts & name2_parts:
            # If at least 2 name parts match, consider it the same author
            return len(name1_parts & name2_parts) >= 2
    
    return False

def clean_old_cache_files():
    """Remove cache files older than today"""
    today_date = datetime.now().strftime("%Y%m%d")
    cache_pattern = "isern_collaboration_cache_scholar_"
    
    try:
        files_in_dir = os.listdir('.')
        old_cache_files = [f for f in files_in_dir if f.startswith(cache_pattern) and not f.endswith(f"{today_date}.json")]
        
        for old_file in old_cache_files:
            try:
                os.remove(old_file)
                print(f"Removed old cache file: {old_file}")
            except Exception as e:
                print(f"Could not remove {old_file}: {e}")
                
    except Exception as e:
        print(f"Error cleaning cache files: {e}")

def build_collaboration_graph():
    """Build the full collaboration graph between ISERN members using Google Scholar"""
    # Check if cached data exists for today
    today_date = datetime.now().strftime("%Y%m%d")
    cache_filename = f"isern_collaboration_cache_scholar_{today_date}.json"
    
    if os.path.exists(cache_filename):
        print(f"Found cached collaboration data for {today_date}")
        print(f"Loading from: {cache_filename}")
        try:
            with open(cache_filename, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Rebuild graph from cache
            G = nx.Graph()
            for member in cache_data.get('members', []):
                G.add_node(member)
            
            for edge in cache_data.get('edges', []):
                G.add_edge(edge[0], edge[1])
                
            print(f"Loaded {G.number_of_nodes()} nodes and {G.number_of_edges()} edges from cache")
            return G
            
        except Exception as e:
            print(f"Error loading cache: {e}")
            print("Will rebuild from scratch...")
    
    # Clean old cache files
    clean_old_cache_files()
    
    # Setup proxy for Google Scholar
    setup_proxy()
    
    # Build collaboration graph from scratch
    print("Building collaboration graph from Google Scholar...")
    G = nx.Graph()
    
    # Add all members as nodes
    for member in isern_members:
        G.add_node(member)
    
    collaboration_data = {}
    
    # For each ISERN member, get their publications and find collaborations
    for i, member in enumerate(isern_members):
        print(f"\nProcessing {i+1}/{len(isern_members)}: {member}")
        
        try:
            # Get publications for this member
            publications = get_author_publications(member, max_results=100)
            
            # Extract coauthors who are ISERN members
            coauthors = extract_coauthors_from_publications(publications, isern_members)
            
            # Remove self from coauthors
            coauthors = [author for author in coauthors if author != member]
            
            collaboration_data[member] = {
                'publications': len(publications),
                'coauthors': coauthors
            }
            
            # Add edges for collaborations
            for coauthor in coauthors:
                if coauthor in isern_members:
                    G.add_edge(member, coauthor)
            
            print(f"  Found {len(coauthors)} ISERN coauthors: {coauthors}")
            
        except Exception as e:
            print(f"  Error processing {member}: {e}")
            collaboration_data[member] = {
                'publications': 0,
                'coauthors': []
            }
    
    # Save cache
    try:
        cache_data = {
            'date': today_date,
            'members': list(G.nodes()),
            'edges': list(G.edges()),
            'collaboration_data': collaboration_data
        }
        
        with open(cache_filename, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCached collaboration data to: {cache_filename}")
        
    except Exception as e:
        print(f"Error saving cache: {e}")
    
    return G

def calculate_isern_numbers(G):
    """Calculate ISERN numbers (distance from founding members) using BFS"""
    isern_numbers = {}
    
    # Start BFS from founding members (ISERN number 0)
    queue = []
    visited = set()
    
    # Initialize founding members with ISERN number 0
    for founder in founding_members:
        if founder in G.nodes():
            isern_numbers[founder] = 0
            queue.append((founder, 0))
            visited.add(founder)
    
    # BFS to assign ISERN numbers
    while queue:
        current_member, current_number = queue.pop(0)
        
        # Check all neighbors (collaborators)
        for neighbor in G.neighbors(current_member):
            if neighbor not in visited:
                isern_numbers[neighbor] = current_number + 1
                queue.append((neighbor, current_number + 1))
                visited.add(neighbor)
    
    # Assign infinity to unconnected members
    for member in G.nodes():
        if member not in isern_numbers:
            isern_numbers[member] = float('inf')
    
    return isern_numbers

def create_interactive_website(G, timestamp):
    """Create an interactive website using vis.js for network visualization"""
    
    # Try to load ISERN numbers if available
    isern_numbers = {}
    isern_file = f"isern_numbers_{timestamp}.json"
    
    if os.path.exists(isern_file):
        try:
            with open(isern_file, 'r') as f:
                data = json.load(f)
                isern_numbers = data.get('isern_numbers', {})
            print(f"Loading ISERN numbers from: {isern_file}")
        except Exception as e:
            print(f"Error loading ISERN numbers: {e}")
    
    if not isern_numbers:
        print("Warning: No ISERN numbers file found. Calculating from graph...")
        isern_numbers = calculate_isern_numbers(G)
    
    # Calculate NetworkX spring layout positions to match PNG
    try:
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    except:
        pos = nx.spring_layout(G)
    
    # Scale positions for vis.js (multiply by 1000 for good spacing)
    for node in pos:
        pos[node] = (pos[node][0] * 1000, pos[node][1] * 1000)
    
    # Define colors for ISERN numbers
    isern_colors = {
        0: '#FF0000',      # Red for founding members
        1: '#FF6600',      # Orange for ISERN number 1
        2: '#FFCC00',      # Yellow for ISERN number 2
        3: '#66FF00',      # Light green for ISERN number 3
        4: '#00FF66',      # Green for ISERN number 4
        5: '#00FFCC',      # Cyan for ISERN number 5
        6: '#0066FF',      # Blue for ISERN number 6
        7: '#6600FF',      # Purple for ISERN number 7
        8: '#CC00FF',      # Magenta for ISERN number 8
        float('inf'): '#CCCCCC'  # Gray for unconnected
    }
    
    # Create nodes data for vis.js
    nodes_data = []
    for node in G.nodes():
        isern_num = isern_numbers.get(node, float('inf'))
        color = isern_colors.get(isern_num, '#CCCCCC')
        
        # Create node label with ISERN number
        if isern_num == float('inf'):
            label = f"{node} (∞)"
        else:
            label = f"{node} ({int(isern_num)})"
        
        # Get position
        x, y = pos.get(node, (0, 0))
        
        nodes_data.append({
            'id': node,
            'label': label,
            'color': {
                'background': color,
                'border': '#000000'
            },
            'font': {
                'color': '#000000' if color != '#FFCC00' else '#000000',  # Ensure readability
                'size': 12,
                'face': 'Arial'
            },
            'shape': 'ellipse',
            'margin': 10,
            'x': x,
            'y': y,
            'physics': False,  # Don't let physics move initial positions
            'isern_number': int(isern_num) if isern_num != float('inf') else 'infinity'
        })
    
    # Create edges data for vis.js
    edges_data = []
    for edge in G.edges():
        edges_data.append({
            'from': edge[0],
            'to': edge[1],
            'color': '#848484',
            'width': 1
        })
    
    # Create legend data
    legend_items = []
    level_counts = {}
    for node, isern_num in isern_numbers.items():
        if isern_num not in level_counts:
            level_counts[isern_num] = 0
        level_counts[isern_num] += 1
    
    for level in sorted(level_counts.keys()):
        if level == float('inf'):
            legend_items.append({
                'label': f'Unconnected ({level_counts[level]} members)',
                'color': isern_colors[level]
            })
        else:
            legend_items.append({
                'label': f'ISERN Number {int(level)} ({level_counts[level]} members)',
                'color': isern_colors[level]
            })
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>ISERN Co-authorship Network (Google Scholar Data)</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        
        .header p {{
            margin: 5px 0;
            color: #666;
        }}
        
        .container {{
            display: flex;
            gap: 20px;
        }}
        
        .sidebar {{
            width: 300px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: fit-content;
        }}
        
        .main-content {{
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }}
        
        #network {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}
        
        .controls {{
            margin-bottom: 30px;
        }}
        
        .controls h3 {{
            margin-top: 0;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }}
        
        .control-group {{
            margin-bottom: 15px;
        }}
        
        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }}
        
        .control-group button {{
            margin: 2px;
            padding: 8px 12px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .control-group button:hover {{
            background: #45a049;
        }}
        
        .legend {{
            margin-bottom: 30px;
        }}
        
        .legend h3 {{
            margin-top: 0;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 5px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border: 1px solid #000;
            border-radius: 50%;
        }}
        
        .stats {{
            margin-bottom: 30px;
        }}
        
        .stats h3 {{
            margin-top: 0;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #FF9800;
            padding-bottom: 5px;
        }}
        
        .stat-item {{
            margin-bottom: 8px;
            font-size: 14px;
            color: #555;
        }}
        
        .node-info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            display: none;
            max-width: 300px;
            z-index: 1000;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ISERN Co-authorship Network</h1>
        <p><strong>Data Source:</strong> Google Scholar</p>
        <p><strong>Visualization:</strong> Interactive network showing collaboration relationships between ISERN members</p>
        <p><strong>Node Colors:</strong> Represent ISERN numbers (distance from founding members)</p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <div class="controls">
                <h3>Controls</h3>
                <div class="control-group">
                    <label>Layout:</label>
                    <button onclick="setLayout('spring')">Spring Layout</button>
                    <button onclick="setLayout('physics')">Physics</button>
                    <button onclick="setLayout('random')">Random</button>
                </div>
                <div class="control-group">
                    <label>Actions:</label>
                    <button onclick="fitNetwork()">Fit to Screen</button>
                    <button onclick="togglePhysics()">Toggle Physics</button>
                    <button onclick="resetZoom()">Reset Zoom</button>
                </div>
            </div>
            
            <div class="legend">
                <h3>ISERN Number Legend</h3>
                {''.join([f'<div class="legend-item"><div class="legend-color" style="background-color: {item["color"]}"></div><span>{item["label"]}</span></div>' for item in legend_items])}
            </div>
            
            <div class="stats">
                <h3>Network Statistics</h3>
                <div class="stat-item"><strong>Total Members:</strong> {G.number_of_nodes()}</div>
                <div class="stat-item"><strong>Collaborations:</strong> {G.number_of_edges()}</div>
                <div class="stat-item"><strong>Connected Components:</strong> {nx.number_connected_components(G)}</div>
                <div class="stat-item"><strong>Network Density:</strong> {nx.density(G):.3f}</div>
            </div>
        </div>
        
        <div class="main-content">
            <div id="network"></div>
            <div id="nodeInfo" class="node-info"></div>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>Instructions:</strong> Click and drag nodes to move them • Zoom with mouse wheel • Click nodes for details • Double-click to focus</p>
        <p><strong>Data Source:</strong> Collaboration data extracted from Google Scholar publications</p>
    </div>

    <script type="text/javascript">
        // Network data
        var nodes = new vis.DataSet({json.dumps(nodes_data, indent=8)});
        
        var edges = new vis.DataSet({json.dumps(edges_data, indent=8)});

        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true,
                selectConnectedEdges: false
            }},
            physics: {{
                enabled: false,
                stabilization: {{ enabled: false }}
            }},
            layout: {{
                hierarchical: {{ enabled: false }}
            }},
            edges: {{
                smooth: {{
                    type: 'continuous'
                }},
                color: {{
                    inherit: false
                }}
            }},
            nodes: {{
                chosen: {{
                    node: function(values, id, selected, hovering) {{
                        values.shadow = true;
                        values.shadowColor = 'rgba(0,0,0,0.3)';
                        values.shadowX = 3;
                        values.shadowY = 3;
                    }}
                }}
            }}
        }};

        // Create network
        var container = document.getElementById('network');
        console.log('Container element:', container);
        
        try {{
            var network = new vis.Network(container, data, options);
            console.log('Network created successfully');
            
            // Set spring layout after creation
            setTimeout(function() {{
                console.log('Setting spring layout');
                setLayout('spring');
            }}, 1000);
            
        }} catch (error) {{
            console.error('Error creating network:', error);
            document.getElementById('network').innerHTML = '<p style="color: red; padding: 20px;">Error creating network: ' + error.message + '</p>';
        }}

        // Event handlers
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                showNodeInfo(node);
            }} else {{
                hideNodeInfo();
            }}
        }});

        network.on("doubleClick", function (params) {{
            if (params.nodes.length > 0) {{
                network.focus(params.nodes[0], {{
                    scale: 1.5,
                    animation: true
                }});
            }}
        }});

        function setLayout(type) {{
            var updateOptions = {{}};
            
            switch(type) {{
                case 'spring':
                    // Reset to original spring layout positions and disable physics
                    updateOptions = {{
                        physics: {{ 
                            enabled: false,
                            stabilization: {{ enabled: false }}
                        }},
                        layout: {{ 
                            hierarchical: {{ enabled: false }}
                        }}
                    }};
                    // Reset node positions to original spring layout
                    nodes.forEach(function(node) {{
                        network.moveNode(node.id, node.x, node.y);
                    }});
                    break;
                case 'physics':
                    updateOptions = {{
                        physics: {{ 
                            enabled: true,
                            stabilization: {{ enabled: true }}
                        }},
                        layout: {{ 
                            hierarchical: {{ enabled: false }},
                            randomSeed: 2 
                        }}
                    }};
                    break;
                case 'random':
                    updateOptions = {{
                        physics: {{ 
                            enabled: false,
                            stabilization: {{ enabled: false }}
                        }},
                        layout: {{ 
                            hierarchical: {{ enabled: false }},
                            randomSeed: Math.floor(Math.random() * 1000) 
                        }}
                    }};
                    break;
            }}
            
            network.setOptions(updateOptions);
            // Fit the network after layout change
            setTimeout(function() {{
                network.fit();
            }}, 500);
        }}

        function fitNetwork() {{
            network.fit();
        }}

        function togglePhysics() {{
            var currentOptions = network.getOptionsFromConfigurator();
            var physicsEnabled = !network.physics.physicsEnabled;
            network.setOptions({{
                physics: {{ enabled: physicsEnabled }}
            }});
        }}

        function resetZoom() {{
            network.moveTo({{
                scale: 1.0
            }});
        }}

        function showNodeInfo(node) {{
            var infoDiv = document.getElementById('nodeInfo');
            var connectedNodes = network.getConnectedNodes(node.id);
            
            var html = '<h4>' + node.label + '</h4>';
            html += '<p><strong>ISERN Number:</strong> ' + node.isern_number + '</p>';
            html += '<p><strong>Collaborators:</strong> ' + connectedNodes.length + '</p>';
            if (connectedNodes.length > 0) {{
                html += '<p><strong>Connected to:</strong><br>';
                connectedNodes.slice(0, 5).forEach(function(nodeId) {{
                    var connectedNode = nodes.get(nodeId);
                    html += '• ' + connectedNode.label + '<br>';
                }});
                if (connectedNodes.length > 5) {{
                    html += '• ... and ' + (connectedNodes.length - 5) + ' more';
                }}
                html += '</p>';
            }}
            
            infoDiv.innerHTML = html;
            infoDiv.style.display = 'block';
        }}

        function hideNodeInfo() {{
            document.getElementById('nodeInfo').style.display = 'none';
        }}
    </script>
</body>
</html>'''
    
    html_filename = f"isern_network_interactive_scholar_{timestamp}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive website created: {html_filename}")
    print("Open this file in a web browser to view the interactive network!")
    print("Features:")
    print("  - Click and drag nodes to move them")
    print("  - Zoom in/out with mouse wheel") 
    print("  - Click nodes for details")
    print("  - Double-click nodes to focus")
    print("  - Use control buttons to change layouts")

def plot_network_graph(G, isern_numbers, timestamp):
    """Create and save a matplotlib visualization of the network"""
    
    print("\nCreating network visualization...")
    
    plt.figure(figsize=(20, 16))
    
    # Use spring layout with same parameters as interactive version
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    
    # Define colors for different ISERN numbers
    isern_colors = {
        0: '#FF0000',      # Red for founding members
        1: '#FF6600',      # Orange for ISERN number 1
        2: '#FFCC00',      # Yellow for ISERN number 2
        3: '#66FF00',      # Light green for ISERN number 3
        4: '#00FF66',      # Green for ISERN number 4
        5: '#00FFCC',      # Cyan for ISERN number 5
        6: '#0066FF',      # Blue for ISERN number 6
        7: '#6600FF',      # Purple for ISERN number 7
        8: '#CC00FF',      # Magenta for ISERN number 8
        float('inf'): '#CCCCCC'  # Gray for unconnected
    }
    
    # Create node colors based on ISERN numbers
    node_colors = []
    for node in G.nodes():
        isern_num = isern_numbers.get(node, float('inf'))
        node_colors.append(isern_colors.get(isern_num, '#CCCCCC'))
    
    # Draw the network
    nx.draw_networkx_edges(G, pos, alpha=0.5, width=0.8, edge_color='gray')
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=300, alpha=0.8)
    
    # Add labels with ISERN numbers
    labels = {}
    for node in G.nodes():
        isern_num = isern_numbers.get(node, float('inf'))
        if isern_num == float('inf'):
            labels[node] = f"{node} (∞)"
        else:
            labels[node] = f"{node} ({int(isern_num)})"
    
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
    
    plt.title('ISERN Co-authorship Network (Google Scholar Data)\nNode colors represent ISERN numbers (distance from founding members)', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Create legend
    legend_elements = []
    level_counts = {}
    for node, isern_num in isern_numbers.items():
        if isern_num not in level_counts:
            level_counts[isern_num] = 0
        level_counts[isern_num] += 1
    
    import matplotlib.patches as mpatches
    for level in sorted(level_counts.keys()):
        if level == float('inf'):
            label = f'Unconnected ({level_counts[level]})'
        else:
            label = f'ISERN Number {int(level)} ({level_counts[level]})'
        legend_elements.append(mpatches.Patch(color=isern_colors[level], label=label))
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save the plot
    plot_filename = f"isern_coauthorship_graph_scholar_{timestamp}.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"Graph visualization saved: {plot_filename}")
    plt.close()

# Main execution
if __name__ == "__main__":
    print("Starting ISERN Co-authorship Network Analysis (Google Scholar)")
    print("=" * 60)
    
    # Build collaboration graph
    G = build_collaboration_graph()
    
    print(f"\nGraph Statistics:")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Number of connected components: {nx.number_connected_components(G)}")
    
    print(f"\nCo-authorship edges between ISERN members:")
    for edge in G.edges():
        print(edge)
    
    # Calculate ISERN numbers
    isern_numbers = calculate_isern_numbers(G)
    
    # Save graph data to files
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Save as GraphML
    graphml_filename = f"isern_coauthorship_graph_scholar_{timestamp}.graphml"
    nx.write_graphml(G, graphml_filename)
    print(f"\nGraph saved as GraphML: {graphml_filename}")
    
    # Save as JSON with metadata
    graph_data = {
        "nodes": list(G.nodes()),
        "edges": list(G.edges()),
        "isern_numbers": {member: (int(num) if num != float('inf') else "infinity") 
                         for member, num in isern_numbers.items()},
        "timestamp": timestamp,
        "data_source": "Google Scholar"
    }
    
    json_filename = f"isern_coauthorship_graph_scholar_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    print(f"Graph saved as JSON: {json_filename}")
    
    # Save edge list
    edgelist_filename = f"isern_coauthorship_edgelist_scholar_{timestamp}.txt"
    nx.write_edgelist(G, edgelist_filename)
    print(f"Graph saved as edge list: {edgelist_filename}")
    
    # Save ISERN numbers separately
    isern_data = {
        "isern_numbers": {member: (int(num) if num != float('inf') else "infinity") 
                         for member, num in isern_numbers.items()},
        "timestamp": timestamp,
        "data_source": "Google Scholar"
    }
    
    isern_filename = f"isern_numbers_{timestamp}.json"
    with open(isern_filename, 'w', encoding='utf-8') as f:
        json.dump(isern_data, f, indent=2, ensure_ascii=False)
    print(f"ISERN numbers saved: {isern_filename}")
    
    # Create interactive website
    create_interactive_website(G, timestamp)
    
    # Create static visualization
    plot_network_graph(G, isern_numbers, timestamp)
    
    print(f"\nAnalysis complete! Files generated:")
    print(f"  - {graphml_filename}")
    print(f"  - {json_filename}")
    print(f"  - {edgelist_filename}")
    print(f"  - {isern_filename}")
    print(f"  - isern_network_interactive_scholar_{timestamp}.html")
    print(f"  - isern_coauthorship_graph_scholar_{timestamp}.png")
