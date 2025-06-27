import requests
import xmltodict
import networkx as nx
import time
import matplotlib.pyplot as plt
import json
import os
import glob
from datetime import datetime
from urllib.parse import quote
from enhanced_name_utils import EnhancedNameMatcher
from isern_utils import load_isern_members

# Initialize enhanced name matcher
name_matcher = EnhancedNameMatcher(similarity_threshold=0.85)

def ask_regenerate_file(filename, description):
    """Ask user if they want to regenerate an existing file"""
    while True:
        response = input(f"{description} file '{filename}' already exists. Regenerate? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

# Load ISERN member list from JSON file
isern_members = load_isern_members('isern_members_enhanced.json')

if not isern_members:
    print("No ISERN members loaded. Exiting.")
    exit(1)

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
                    if name_matcher.is_likely_same_person(author_name, main_author):
                        variations.append(main_author)
                    
                    # Add aliases if they exist
                    if 'aliases' in hit['info'] and 'alias' in hit['info']['aliases']:
                        aliases = hit['info']['aliases']['alias']
                        if not isinstance(aliases, list):
                            aliases = [aliases]
                        
                        for alias in aliases:
                            if name_matcher.is_likely_same_person(author_name, alias):
                                variations.append(alias)
        
        # Remove duplicates
        unique_variations = list(dict.fromkeys(variations))  # Preserves order
        
        return unique_variations
        
    except Exception as e:
        print(f"    Error in DBLP author search: {e}")
        return []
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

def load_isern_numbers():
    """Load ISERN numbers from the JSON file"""
    try:
        filename = "isern_numbers.json"
        print(f"Loading ISERN numbers from: {filename}")
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Convert infinity strings back to float('inf')
        isern_numbers = {}
        for member, number in data['isern_numbers'].items():
            if number == "infinity":
                isern_numbers[member] = float('inf')
            else:
                isern_numbers[member] = int(number)
        
        return isern_numbers
    except Exception as e:
        print(f"Error loading ISERN numbers: {e}")
        return None

def clean_data_for_json(data):
    """Clean data to ensure it's JSON serializable without NaN or Infinity values"""
    import math
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return 0  # Replace NaN/Inf with 0
        return data
    else:
        return data

def create_interactive_website(G):
    """Create an interactive website with draggable nodes using vis.js"""
    
    # Load ISERN numbers for coloring
    isern_numbers = load_isern_numbers()
     # Calculate top collaborators
    degree_centrality = nx.degree_centrality(G)
    sorted_centrality = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
    top_collaborators = sorted_centrality[:10]
    
    # Calculate degree centrality for circular positioning
    max_centrality = max(degree_centrality.values()) if degree_centrality else 1
    
    # Prepare data for vis.js
    nodes_data = []
    edges_data = []
    
    # Define colors for ISERN number levels (matching the style from isern-number-graph.py)
    level_colors = {
        0: {'background': '#8B0000', 'font': '#FFFFFF'},    # Dark red background, white text
        1: {'background': '#FF4500', 'font': '#FFFFFF'},    # Orange red background, white text
        2: {'background': '#DAA520', 'font': '#000000'},    # Goldenrod background, black text
        3: {'background': '#228B22', 'font': '#FFFFFF'},    # Forest green background, white text
        4: {'background': '#4169E1', 'font': '#FFFFFF'},    # Royal blue background, white text
        5: {'background': '#8B008B', 'font': '#FFFFFF'},    # Dark magenta background, white text
        6: {'background': '#DC143C', 'font': '#FFFFFF'},    # Crimson background, white text
        7: {'background': '#8B4513', 'font': '#FFFFFF'},    # Saddle brown background, white text
        float('inf'): {'background': '#404040', 'font': '#FFFFFF'}  # Dark gray background, white text
    }
    
    # Calculate positions using the same spring layout as the PNG
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    
    # Scale positions for vis.js (multiply by a factor to make the layout larger)
    scale_factor = 800
    for node in pos:
        pos[node] = (pos[node][0] * scale_factor, pos[node][1] * scale_factor)
    
    # Create nodes with styling based on ISERN numbers and spring layout positioning
    for node in G.nodes():
        degree = G.degree(node)
        
        # Get position from spring layout
        x, y = pos[node]
        
        # Determine ISERN number and color
        if isern_numbers and node in isern_numbers:
            isern_number = isern_numbers[node]
            # Convert infinite values to a large finite number for vis.js
            level_for_layout = 999 if isern_number == float('inf') else int(isern_number)
            
            if isern_number in level_colors:
                color_config = level_colors[isern_number]
                background_color = color_config['background']
                font_color = color_config['font']
            else:
                background_color = '#708090'  # Slate gray for levels not in our color map
                font_color = '#FFFFFF'  # White text for visibility
            
            # Create tooltip with both ISERN number and collaborations
            isern_display = "∞" if isern_number == float('inf') else str(int(isern_number))
            title = f"{node}<br>ISERN Number: {isern_display}<br>Collaborations: {degree}"
            label = f"{node} ({isern_display})"
            
        else:
            # Fallback to degree-based coloring if ISERN numbers not available
            background_color = '#4488ff'  # Default blue
            font_color = '#FFFFFF'  # White text
            title = f"{node}<br>Collaborations: {degree}"
            label = node  # No ISERN number available
            level_for_layout = 999  # Put unknown nodes at bottom level
        
        # Ensure positions are finite numbers
        x = float(x) if not (isinstance(x, float) and (x != x or x == float('inf') or x == float('-inf'))) else 0.0
        y = float(y) if not (isinstance(y, float) and (y != y or y == float('inf') or y == float('-inf'))) else 0.0
            
        nodes_data.append({
            "id": node,
            "label": label,
            "title": title,
            "level": level_for_layout,  # Use finite number for hierarchical layout
            "x": x,  # Initial x position for circular layout
            "y": y,  # Initial y position for circular layout
            "shape": "ellipse",  # Oval shape that expands to fit text
            "color": {
                "background": background_color,
                "border": "#000000",
                "highlight": {
                    "background": background_color,
                    "border": "#000000"
                }
            },
            "font": {
                "color": font_color,
                "size": 14,
                "face": "Arial",
                "bold": {"color": font_color}  # Ensure bold text also uses high-contrast color
            },
            "margin": {
                "top": 8,
                "bottom": 8,
                "left": 12,
                "right": 12
            },  # Padding around the text for better oval shape
            "widthConstraint": {
                "minimum": 100,  # Slightly larger minimum for better oval appearance
                "maximum": 250   # Allow for longer names
            },
            "heightConstraint": {
                "minimum": 35,   # Slightly taller minimum for better proportion
                "valign": "middle"  # Center text vertically
            }
        })
    
    # Create edges
    for edge in G.edges():
        edges_data.append({
            "from": edge[0],
            "to": edge[1],
            "width": 1,
            "color": "#999999"
        })
    
    # Create the HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISERN Co-authorship Network - Colored by ISERN Number</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        // Fallback if vis is not loaded
        if (typeof vis === 'undefined') {{
            document.write('<script src="https://cdn.jsdelivr.net/npm/vis-network@latest/standalone/umd/vis-network.min.js"><\/script>');
        }}
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            background-color: #34495e;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
            margin: 5px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .controls {{
            padding: 20px;
            border-bottom: 1px solid #eee;
            background-color: #f8f9fa;
        }}
        
        .controls h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
        }}
        
        .control-group {{
            margin-bottom: 15px;
        }}
        
        .control-group label {{
            display: inline-block;
            width: 120px;
            font-weight: bold;
        }}
        
        button {{
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 2px;
        }}
        
        button:hover {{
            background-color: #2980b9;
        }}
        
        #network {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
        }}
        
        .legend {{
            padding: 20px;
            background-color: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        
        .legend h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
        }}
        
        .legend-item {{
            display: inline-block;
            margin: 5px 15px 5px 0;
            font-size: 0.9em;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            vertical-align: middle;
        }}
        
        .collaborators-table {{
            padding: 20px;
            background-color: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        
        .collaborators-table h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
        }}
        
        .collaborators-table table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .collaborators-table th,
        .collaborators-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        .collaborators-table th {{
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
        }}
        
        .collaborators-table tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .isern-number-cell {{
            text-align: center;
            font-weight: bold;
        }}
        
        .info-panel {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            max-width: 300px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }}
        
        .info-panel h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ISERN Co-authorship Network</h1>
            <p>Interactive visualization of research collaborations within the International Software Engineering Research Network</p>
            <p><strong>Spring Layout</strong> - Same layout as the static PNG visualization for consistency</p>
            <p><strong>Nodes colored by ISERN Number</strong> - Distance from founding members (Koji Torii, Dieter Rombach, Victor Basili, Ross Jeffery, Giovanni Cantone, Markku Oivo)</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{G.number_of_nodes()}</span>
                <span class="stat-label">Researchers</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{G.number_of_edges()}</span>
                <span class="stat-label">Collaborations</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{nx.number_connected_components(G)}</span>
                <span class="stat-label">Components</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{nx.density(G):.3f}</span>
                <span class="stat-label">Density</span>
            </div>
        </div>
        
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
        
        <div id="network"></div>
        
        <div class="legend">
            <h3>Legend - ISERN Numbers</h3>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #8B0000;"></span>
                Level 0 (Founding Members)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #FF4500;"></span>
                Level 1 (Direct collaborators)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #DAA520;"></span>
                Level 2 (Second degree)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #228B22;"></span>
                Level 3 (Third degree)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #404040;"></span>
                Disconnected (∞)
            </div>
        </div>
        
        <div class="collaborators-table">
            <h3>Top 10 Collaborators</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Researcher</th>
                        <th>ISERN Number</th>
                        <th>Collaborations</th>
                        <th>Centrality</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add table rows for top collaborators
    for i, (researcher, centrality) in enumerate(top_collaborators, 1):
        degree = G.degree(researcher)
        if isern_numbers and researcher in isern_numbers:
            isern_number = isern_numbers[researcher]
            isern_display = "∞" if isern_number == float('inf') else str(int(isern_number))
        else:
            isern_display = "N/A"
        
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td><strong>{researcher}</strong></td>
                        <td class="isern-number-cell">{isern_display}</td>
                        <td>{degree}</td>
                        <td>{centrality:.4f}</td>
                    </tr>"""
    
    html_content += """
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="info-panel" class="info-panel">
        <h4 id="node-name"></h4>
        <p id="node-details"></p>
    </div>

    <script type="text/javascript">
        // Check if vis.js is loaded
        if (typeof vis === 'undefined') {
            document.getElementById('network').innerHTML = '<p style="color: red; padding: 20px; text-align: center;">Error: vis.js library failed to load. Please check your internet connection or try refreshing the page.</p>';
        } else {
            console.log('vis.js loaded successfully');
        }
        
        // Network data"""
    
    # Add the JavaScript data separately to avoid f-string complexity
    nodes_json = json.dumps(clean_data_for_json(nodes_data), indent=2)
    edges_json = json.dumps(clean_data_for_json(edges_data), indent=2)
    
    html_content += f"""
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});
        
        // Network options"""
    
    html_content += """
        var options = {
            physics: {
                enabled: false  // Start with fixed positions for circular layout
            },
            nodes: {
                borderWidth: 2,
                shadow: true,
                chosen: {
                    node: function(values, id, selected, hovering) {
                        // Highlight the node but keep original font color
                        if (values.color && typeof values.color === 'object') {
                            values.color.background = '#ff6b6b';
                            values.color.border = '#ff0000';
                        } else {
                            values.color = '#ff6b6b';
                        }
                        values.size = values.size * 1.2;
                    }
                }
            },
            edges: {
                color: {
                    color: '#999999',
                    highlight: '#ff6b6b'
                },
                width: 1,
                smooth: {
                    enabled: true,
                    type: 'continuous'
                }
            },
            physics: {
                enabled: true,
                stabilization: {
                    enabled: true,
                    iterations: 1000
                }
            },
            interaction: {
                dragNodes: true,
                dragView: true,
                zoomView: true,
                selectConnectedEdges: true,
                hover: true,
                tooltipDelay: 300
            }
        };
        
        // Create network
        var container = document.getElementById('network');
        var data = {
            nodes: nodes,
            edges: edges
        };
        
        console.log('Creating network with', nodes.length, 'nodes and', edges.length, 'edges');
        console.log('Container element:', container);
        
        try {
            var network = new vis.Network(container, data, options);
            console.log('Network created successfully');
            
            // Set spring layout after creation
            setTimeout(function() {
                console.log('Setting spring layout');
                setLayout('spring');
            }, 1000);
            
        } catch (error) {
            console.error('Error creating network:', error);
            document.getElementById('network').innerHTML = '<p style="color: red; padding: 20px;">Error creating network: ' + error.message + '</p>';
        }
        
        // Event handlers
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                var connectedEdges = network.getConnectedEdges(nodeId);
                
                document.getElementById('node-name').textContent = node.label;
                document.getElementById('node-details').innerHTML = 
                    'Collaborations: ' + connectedEdges.length + '<br>' +
                    'Click and drag to move this node<br>' +
                    'Double-click to focus on this researcher';
                document.getElementById('info-panel').style.display = 'block';
            } else {
                document.getElementById('info-panel').style.display = 'none';
            }
        });
        
        network.on('doubleClick', function(params) {
            if (params.nodes.length > 0) {
                network.focus(params.nodes[0], {
                    scale: 1.5,
                    animation: true
                });
            }
        });
        
        // Control functions
        function setLayout(type) {
            var updateOptions = {};
            
            switch(type) {
                case 'spring':
                    // Reset to original spring layout positions and disable physics
                    updateOptions = {
                        physics: { 
                            enabled: false,
                            stabilization: { enabled: false }
                        },
                        layout: { 
                            hierarchical: { enabled: false }
                        }
                    };
                    // Reset node positions to original spring layout
                    nodes.forEach(function(node) {
                        network.moveNode(node.id, node.x, node.y);
                    });
                    break;
                case 'physics':
                    updateOptions = {
                        physics: { 
                            enabled: true,
                            stabilization: { enabled: true }
                        },
                        layout: { 
                            hierarchical: { enabled: false },
                            randomSeed: 2 
                        }
                    };
                    break;
                case 'random':
                    updateOptions = {
                        physics: { 
                            enabled: false,
                            stabilization: { enabled: false }
                        },
                        layout: { 
                            hierarchical: { enabled: false },
                            randomSeed: Math.floor(Math.random() * 1000) 
                        }
                    };
                    break;
            }
            
            network.setOptions(updateOptions);
            // Fit the network after layout change
            setTimeout(function() {
                network.fit();
            }, 100);
        }
        
        function fitNetwork() {
            network.fit();
        }
        
        function togglePhysics() {
            var currentPhysics = network.physics.physicsEnabled;
            network.setOptions({ physics: { enabled: !currentPhysics } });
        }
        
        function resetZoom() {
            network.moveTo({
                position: {x: 0, y: 0},
                scale: 1,
                animation: true
            });
        }
        
        // Hide info panel when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('#info-panel') && !event.target.closest('#network')) {
                document.getElementById('info-panel').style.display = 'none';
            }
        });
    </script>
</body>
</html>"""

    # Save the HTML file
    html_filename = "isern_network_interactive.html"
    
    # Check if file exists and ask for confirmation
    if os.path.exists(html_filename):
        if not ask_regenerate_file(html_filename, "Interactive HTML"):
            print(f"Skipping generation of {html_filename}")
            return
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive website created: {html_filename}")
    print(f"Open this file in a web browser to view the interactive network!")
    print(f"Features:")
    print(f"  - Click and drag nodes to move them")
    print(f"  - Zoom in/out with mouse wheel")
    print(f"  - Click nodes for details")
    print(f"  - Double-click nodes to focus")
    print(f"  - Use control buttons to change layouts")

def load_collaboration_network():
    """Load the collaboration network from the full discovery results"""
    try:
        with open('isern_full_collaboration_network.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None

def create_graph_from_precomputed_data(collab_data):
    """Create NetworkX graph from pre-computed collaboration data"""
    print("🎨 Creating graph from pre-computed collaboration data...")
    
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
    
    print(f"✅ Graph created from pre-computed data:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    print(f"   Density: {nx.density(G):.3f}")
    
    return G

def create_graph_from_dblp():
    """Create graph by querying DBLP (legacy method)"""
    cache_filename = "isern_collaboration_cache.graphml"
    
    # Check if cache exists and ask for confirmation
    rebuild_cache = True
    if os.path.exists(cache_filename):
        rebuild_cache = ask_regenerate_file(cache_filename, "Collaboration cache")

    if rebuild_cache:
        if os.path.exists(cache_filename):
            print(f"Regenerating collaboration graph...")
        else:
            print("Building new collaboration graph...")
        
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
                        # Check if this coauthor is also an ISERN member using enhanced matching
                        if is_isern_member(coauthor):
                            # Find the best matching ISERN member name
                            matches = name_matcher.find_best_matches(coauthor, isern_members, top_k=1)
                            if matches:
                                other_member = matches[0][0]
                                if other_member != member:
                                    G.add_edge(member, other_member)
                                    print(f"  Found collaboration: {member} <-> {other_member} (via coauthor '{coauthor}')")
                                    break
                
                # Be respectful to DBLP API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing {member}: {e}")
        
        # Save to cache
        print(f"Saving collaboration graph to cache: {cache_filename}")
        nx.write_graphml(G, cache_filename)
    else:
        print(f"Loading collaboration graph from cache: {cache_filename}")
        G = nx.read_graphml(cache_filename)
        # Convert node labels back to strings (GraphML may store them differently)
        G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
        print(f"Loaded {G.number_of_nodes()} nodes and {G.number_of_edges()} edges from cache")
    
    return G

# Build co-authorship graph - try pre-computed data first
print("🚀 ISERN COLLABORATION GRAPH GENERATION")
print("=" * 45)

collab_data = load_collaboration_network()

if collab_data:
    print("✅ Found pre-computed collaboration data from full_isern_collaboration_discovery.py")
    G = create_graph_from_precomputed_data(collab_data)
else:
    print("❌ Pre-computed collaboration data not found.")
    print("   File: isern_full_collaboration_network.json")
    print("\n💡 Recommendation:")
    print("   Run 'python full_isern_collaboration_discovery.py' first for:")
    print("   - More comprehensive collaboration discovery")
    print("   - Faster processing (uses pre-computed data)")
    print("   - Better accuracy (member-to-member approach)")
    
    response = input("\nDo you want to continue with legacy DBLP querying? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Exiting. Please run 'python full_isern_collaboration_discovery.py' first.")
        exit(0)
    
    print("\n⚠️  Using legacy DBLP querying method...")
    G = create_graph_from_dblp()

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
graphml_filename = "isern_coauthorship_graph.graphml"
json_filename = "isern_coauthorship_graph.json"
edgelist_filename = "isern_coauthorship_edgelist.txt"
plot_filename = "isern_coauthorship_graph.png"

# Check each output file and ask for confirmation
save_graphml = True
save_json = True
save_edgelist = True
save_plot = True
generate_interactive = True

if os.path.exists(graphml_filename):
    save_graphml = ask_regenerate_file(graphml_filename, "GraphML")

if os.path.exists(json_filename):
    save_json = ask_regenerate_file(json_filename, "JSON")

if os.path.exists(edgelist_filename):
    save_edgelist = ask_regenerate_file(edgelist_filename, "Edge list")

if os.path.exists(plot_filename):
    save_plot = ask_regenerate_file(plot_filename, "PNG plot")

if os.path.exists("isern_network_interactive.html"):
    generate_interactive = ask_regenerate_file("isern_network_interactive.html", "Interactive HTML")

# Save files based on user choices
if save_graphml:
    nx.write_graphml(G, graphml_filename)
    print(f"Graph saved as GraphML: {graphml_filename}")

if save_json:
    graph_data = {
        "nodes": [{"id": node, "label": node} for node in G.nodes()],
        "edges": [{"source": edge[0], "target": edge[1]} for edge in G.edges()],
        "metadata": {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "connected_components": nx.number_connected_components(G)
        }
    }
    
    with open(json_filename, 'w') as f:
        json.dump(graph_data, f, indent=2)
    print(f"Graph saved as JSON: {json_filename}")

if save_edgelist:
    nx.write_edgelist(G, edgelist_filename)
    print(f"Graph saved as edge list: {edgelist_filename}")

# Create interactive web visualization
if generate_interactive:
    create_interactive_website(G)

# Create visualization with oval nodes that expand to fit names
from matplotlib.patches import Ellipse
import matplotlib.patches as patches

plt.figure(figsize=(20, 16))
ax = plt.gca()
pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

# Load ISERN numbers for coloring (same as interactive version)
isern_numbers = load_isern_numbers()

# Define colors for ISERN number levels (matching the interactive version)
level_colors = {
    0: '#8B0000',    # Dark red
    1: '#FF4500',    # Orange red
    2: '#DAA520',    # Goldenrod
    3: '#228B22',    # Forest green
    4: '#4169E1',    # Royal blue
    5: '#8B008B',    # Dark magenta
    6: '#DC143C',    # Crimson
    7: '#8B4513',    # Saddle brown
    float('inf'): '#404040'  # Dark gray
}

# First draw all edges
nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.6, width=2, ax=ax)

# Create custom oval nodes that expand to fit text
font_size = 9
for node in G.nodes():
    x, y = pos[node]
    
    # Determine color based on ISERN number
    if isern_numbers and node in isern_numbers:
        isern_number = isern_numbers[node]
        node_color = level_colors.get(isern_number, '#708090')  # Default gray
        isern_display = "∞" if isern_number == float('inf') else str(int(isern_number))
        label = f"{node} ({isern_display})"
    else:
        node_color = '#4488ff'  # Default blue
        label = node
    
    # Measure text dimensions to size the oval appropriately
    text_bbox = ax.text(x, y, label, fontsize=font_size, ha='center', va='center', 
                       bbox=dict(boxstyle='round,pad=0', alpha=0)).get_window_extent()
    
    # Convert bbox to data coordinates
    text_bbox_data = text_bbox.transformed(ax.transData.inverted())
    text_width = text_bbox_data.width
    text_height = text_bbox_data.height
    
    # Add padding and create oval dimensions
    padding_x = text_width * 0.6  # 60% padding horizontally
    padding_y = text_height * 0.8  # 80% padding vertically
    
    oval_width = text_width + padding_x
    oval_height = text_height + padding_y
    
    # Ensure minimum size for better appearance
    oval_width = max(oval_width, 0.08)
    oval_height = max(oval_height, 0.05)
    
    # Create and add the oval
    oval = Ellipse((x, y), oval_width, oval_height, 
                  facecolor=node_color, edgecolor='black', 
                  linewidth=1.5, alpha=0.8, zorder=2)
    ax.add_patch(oval)
    
    # Determine text color for high contrast
    # Convert hex to RGB to calculate brightness
    hex_color = node_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = sum(rgb) / 3
    text_color = 'white' if brightness < 128 else 'black'
    
    # Add the text label
    ax.text(x, y, label, fontsize=font_size, ha='center', va='center',
           color=text_color, fontweight='bold', zorder=3)

plt.title("ISERN Members Co-authorship Network", fontsize=16, fontweight='bold')

# Add legend for ISERN number colors
legend_elements = []
for level, color in level_colors.items():
    if level == float('inf'):
        label = "Disconnected (∞)"
    elif level == 0:
        label = "Level 0 (Founding Members)"
    else:
        label = f"Level {int(level)}"
    
    legend_elements.append(patches.Patch(color=color, label=label))

# Only show legend if we have ISERN numbers loaded
if isern_numbers:
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
              frameon=True, fancybox=True, shadow=True, fontsize=10)

plt.axis('off')
plt.tight_layout()

# Save the plot
plot_filename = "isern_coauthorship_graph.png"
if save_plot:
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

