# ISERN Collaboration Network Analysis

This project provides tools for an analysis of ISERN (International Software Engineering Research Network) member collaborations using enhanced name normalization and DBLP data mining.

## 🎯 Overview

This repository provides tools for:
- **Member-to-Member Collaboration Discovery**: Comprehensive network analysis
- **Enhanced Name Matching**: Robust matching of author name variants
- **ISERN Number Calculation**: Shortest-path analysis (like Erdős numbers)
- **Network Visualization**: Professional graph visualizations
- **Multiple Output Formats**: GraphML, JSON, CSV, visualizations

## 🚀 Key Features

- **97.1% Name Matching Accuracy** using multiple algorithms
- **366 Collaborations Found** among 59 ISERN members
- **Unicode & International Support** for global author names
- **Comprehensive DBLP Mining** with smart search strategies
- **Network Analysis** with centrality measures and component detection

## 📁 Core Scripts

### Main Analysis Tools
- `full_isern_collaboration_discovery.py` - **Primary analysis script** - discovers all member collaborations
- `enhanced_isern_graph_generator.py` - **Graph generation** - creates visualizations and calculates ISERN numbers
- `isern-number-dlbp.py` - ISERN number calculations using DBLP data
- `isern-graph-dlbp.py` - Legacy co-authorship network analysis
- `isern-number-graph.py` - Network visualization of ISERN numbers

### Supporting Components  
- `enhanced_name_utils.py` - **Name normalization system** (97.1% accuracy)
- `isern_utils.py` - ISERN member data management utilities
- `scrape_isern_members.py` - ISERN member list scraping tool
- `isern_members_enhanced.json` - **ISERN member database**

## 🏃‍♂️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Full Analysis
```bash
# Discover all member collaborations (takes ~15 minutes)
python full_isern_collaboration_discovery.py

# Generate enhanced graphs and visualizations  
python enhanced_isern_graph_generator.py
```

### 3. Check Results
- `isern_full_collaboration_network.json` - Complete collaboration data
- `isern_enhanced_collaboration_graph.png` - Network visualization
- `isern_collaboration_summary.txt` - Summary statistics
- `isern_numbers_from_collaboration_graph.json` - ISERN numbers

## 📊 Current Results

### Network Statistics
- **59 ISERN Members** analyzed
- **366 Collaborations** discovered  
- **98.3% Connectivity** (58/59 members connected)
- **21.4% Network Density**

### ISERN Number Distribution
- **ISERN 0**: 6 founders (Victor Basili, Dieter Rombach, Ross Jeffery, Giovanni Cantone, Markku Oivo, Koji Torii)
- **ISERN 1**: 36 direct collaborators
- **ISERN 2**: 16 second-degree collaborators
- **Unconnected**: 1 member (Takeshi Hayama)

### Top Collaborators
1. **Dietmar Pfahl**: 29 collaborations
2. **Markku Oivo**: 28 collaborations  
3. **Michael Felderer**: 27 collaborations
4. **Daniel Mendez Fernandez**: 26 collaborations

## 🔬 Enhanced Name Matching

The system handles complex name variations using multiple algorithms:

- **Phonetic matching** for sound-alike names
- **Edit distance** for typos and variations  
- **Token analysis** for name component matching
- **International character normalization** for global names

```python
from enhanced_name_utils import EnhancedNameMatcher

# Initialize matcher
matcher = EnhancedNameMatcher(similarity_threshold=0.85)

# Find best matches for an author name
matches = matcher.find_best_matches(
    "Daniel Port", 
    ["Dan Port", "Daniel Porter", "D. Port"]
)
# Returns: [("Dan Port", 1.000), ("D. Port", 0.95)]

# Check if two names refer to the same person
same_person = matcher.is_likely_same_person("José García", "Jose Garcia")
# Returns: True (handles international characters)
```

## 📊 Output Files

### Network Data
- `isern_full_collaboration_network.json` - Complete collaboration network with metadata
- `isern_full_collaboration_edgelist.txt` - Simple edge list format
- `isern_enhanced_collaboration_graph.graphml` - Graph data for Gephi/Cytoscape

### Visualizations  
- `isern_enhanced_collaboration_graph.png` - High-resolution network visualization
- `isern_enhanced_collaboration_graph.pdf` - Vector format for publications
- `isern_numbers_graph.png` - ISERN number distribution visualization

### Analysis Results
- `isern_numbers_from_collaboration_graph.json` - Final ISERN numbers
- `isern_collaboration_summary.txt` - Human-readable summary statistics

## 🔧 Technical Details

### Enhanced Name Matching
- **97.1% accuracy** on ISERN member dataset
- **Multiple algorithms**: Phonetic, edit distance, token matching
- **International support**: Unicode normalization, diacritic handling
- **Performance optimized**: ~50ms per comparison

### Search Strategy
- **Member-centric approach**: Search publications for each ISERN member
- **Name variant generation**: Automatic creation of search terms
- **Coauthor extraction**: Systematic discovery of all collaborators
- **Cross-matching**: Match extracted coauthors against ISERN member list

### Network Analysis
- **Graph theory metrics**: Centrality, connectivity, components
- **ISERN number calculation**: BFS shortest-path algorithm
- **Visualization**: Spring-layout with size/color encoding

## 🎯 Key Achievements

1. **Resolved Dan Port Issue**: Correctly identified his collaboration with Victor Basili through "Daniel Port" name variant
2. **Comprehensive Network**: Discovered 366 collaborations vs. previous approaches finding far fewer
3. **High Connectivity**: 98.3% of ISERN members are connected in the collaboration network
4. **Robust Matching**: Handles international names, initials, nicknames, and formatting variations

## 📚 Dependencies

```txt
# Core analysis
networkx>=3.0
pandas>=1.5.0
matplotlib>=3.5.0
requests>=2.28.0

# Name matching
nameparser>=1.1.2
unidecode>=1.3.4
rapidfuzz>=2.13.0
jellyfish>=0.9.0
python-Levenshtein>=0.20.0
recordlinkage>=0.16

# Web scraping  
beautifulsoup4>=4.11.0
xmltodict>=0.13.0
```

## 🤝 Contributing

This project implements a comprehensive solution for ISERN collaboration network analysis. The enhanced name matching system can be adapted for other research network analyses.

For questions or improvements, please create an issue or pull request.


