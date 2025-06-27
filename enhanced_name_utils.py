#!/usr/bin/env python3
"""
Enhanced Name Normalization and Matching Utilities

This module provides state-of-the-art name normalization and matching
using multiple robust libraries for maximum accuracy and coverage.
"""

from nameparser import HumanName
from unidecode import unidecode
from rapidfuzz import fuzz, process
import jellyfish
import recordlinkage
import re
from typing import List, Tuple, Dict, Set, Optional
import pandas as pd


class EnhancedNameMatcher:
    """
    Professional-grade name normalization and matching using multiple algorithms
    """
    
    # Extended nickname mappings
    NICKNAME_MAP = {
        # English names
        'alexander': ['alex', 'al', 'xander', 'sander', 'lex'],
        'alexandra': ['alex', 'sandra', 'sasha', 'lexie'],
        'andrew': ['andy', 'drew', 'andre'],
        'anthony': ['tony', 'ant'],
        'barbara': ['barb', 'babs', 'bobbie'],
        'benjamin': ['ben', 'benny', 'benji'],
        'christopher': ['chris', 'kit', 'topher'],
        'daniel': ['dan', 'danny', 'dane'],
        'david': ['dave', 'davey', 'davide'],
        'elizabeth': ['liz', 'beth', 'betty', 'eliza', 'libby'],
        'frederick': ['fred', 'rick', 'freddy'],
        'gregory': ['greg', 'gregor'],
        'jennifer': ['jen', 'jenny', 'jenna'],
        'jonathan': ['jon', 'johnny', 'nathan'],
        'katherine': ['kate', 'kathy', 'katie', 'kathryn', 'kat'],
        'matthew': ['matt', 'mateo'],
        'michael': ['mike', 'mick', 'mickey', 'michel'],
        'nicholas': ['nick', 'nicky', 'nico', 'nicolas'],
        'patricia': ['pat', 'patty', 'tricia', 'patsy'],
        'rebecca': ['becky', 'becca', 'becki'],
        'richard': ['rick', 'dick', 'rich', 'ricky'],
        'robert': ['rob', 'bob', 'bobby', 'roberto'],
        'stephanie': ['steph', 'stefanie'],
        'theodore': ['ted', 'theo', 'thaddeus'],
        'thomas': ['tom', 'tommy', 'tomas'],
        'william': ['will', 'bill', 'billy', 'liam', 'willem'],
        
        # International variations
        'giovanni': ['john', 'gian', 'gianni'],
        'giuseppe': ['joseph', 'joe', 'pepe'],
        'francesco': ['francis', 'franco'],
        'antonio': ['anthony', 'tony'],
        'marco': ['mark', 'marcus'],
        'andrea': ['andrew', 'andre'],
        'matteo': ['matthew', 'matt'],
        'alessandro': ['alexander', 'alex'],
        'stefano': ['stephen', 'steve'],
        'roberto': ['robert', 'rob'],
        
        # German variations
        'wilhelm': ['william', 'will'],
        'johann': ['john', 'johannes'],
        'friedrich': ['frederick', 'fritz'],
        'heinrich': ['henry', 'henri'],
        'ludwig': ['louis', 'luis'],
        'karl': ['charles', 'carl'],
        'andreas': ['andrew', 'andre'],
        'michael': ['michel', 'mikael'],
        'stefan': ['stephen', 'steve'],
        'christoph': ['christopher', 'chris'],
        
        # French variations
        'jean': ['john', 'johannes'],
        'pierre': ['peter', 'pedro'],
        'jacques': ['james', 'jacob'],
        'philippe': ['philip', 'filip'],
        'michel': ['michael', 'mike'],
        'françois': ['francis', 'franco'],
        'andré': ['andrew', 'andre'],
        'charles': ['karl', 'carlos'],
        'henri': ['henry', 'heinrich'],
        'louis': ['ludwig', 'luis'],
        
        # Spanish variations
        'josé': ['joseph', 'joe'],
        'juan': ['john', 'johannes'],
        'antonio': ['anthony', 'tony'],
        'francisco': ['francis', 'franco'],
        'manuel': ['emmanuel', 'manuel'],
        'pedro': ['peter', 'pierre'],
        'luis': ['louis', 'ludwig'],
        'carlos': ['charles', 'karl'],
        'miguel': ['michael', 'mike'],
        'rafael': ['raphael', 'rafa'],
    }
    
    # Common middle name patterns
    MIDDLE_NAME_PATTERNS = [
        r'\b[A-Z]\.',  # Single initial with period
        r'\b[A-Z]\b',  # Single initial without period
        r'\b[A-Z][a-z]+\b',  # Full middle name
    ]
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the enhanced name matcher
        
        Args:
            similarity_threshold (float): Minimum similarity score for matches
        """
        self.similarity_threshold = similarity_threshold
        self.indexer = recordlinkage.Index()
        self.compare = recordlinkage.Compare()
        
    def normalize_name(self, name: str) -> str:
        """
        Normalize a name using multiple techniques
        
        Args:
            name (str): Raw name string
            
        Returns:
            str: Normalized name
        """
        if not name or not isinstance(name, str):
            return ""
            
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Handle common prefixes and suffixes
        name = re.sub(r'\b(Dr|Prof|Professor|Mr|Mrs|Ms|Miss)\.?\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(Jr|Sr|III|IV|PhD|MD)\.?$', '', name, flags=re.IGNORECASE)
        
        # Parse with nameparser
        parsed = HumanName(name)
        
        # Normalize Unicode characters
        first = unidecode(parsed.first.lower()) if parsed.first else ""
        last = unidecode(parsed.last.lower()) if parsed.last else ""
        middle = unidecode(parsed.middle.lower()) if parsed.middle else ""
        
        # Clean up punctuation and special characters
        first = re.sub(r'[^\w\s-]', '', first)
        last = re.sub(r'[^\w\s-]', '', last)
        middle = re.sub(r'[^\w\s-]', '', middle)
        
        # Construct normalized name
        parts = [p for p in [first, middle, last] if p]
        return ' '.join(parts)
    
    def generate_name_variations(self, name: str) -> Set[str]:
        """
        Generate various forms and variations of a name
        
        Args:
            name (str): Input name
            
        Returns:
            Set[str]: Set of name variations
        """
        variations = set()
        normalized = self.normalize_name(name)
        
        if not normalized:
            return variations
            
        # Add the normalized version
        variations.add(normalized)
        
        # Parse the name
        parsed = HumanName(name)
        first = parsed.first.lower() if parsed.first else ""
        last = parsed.last.lower() if parsed.last else ""
        middle = parsed.middle.lower() if parsed.middle else ""
        
        # Add basic variations
        if first and last:
            variations.add(f"{first} {last}")
            variations.add(f"{last} {first}")
            
            # Add variations with middle initial
            if middle:
                middle_initial = middle[0]
                variations.add(f"{first} {middle_initial} {last}")
                variations.add(f"{first} {middle_initial}. {last}")
                variations.add(f"{last} {first} {middle_initial}")
                
                # Full middle name
                variations.add(f"{first} {middle} {last}")
        
        # Add nickname variations
        if first in self.NICKNAME_MAP:
            for nickname in self.NICKNAME_MAP[first]:
                if last:
                    variations.add(f"{nickname} {last}")
                    if middle:
                        variations.add(f"{nickname} {middle[0]} {last}")
                        variations.add(f"{nickname} {middle} {last}")
        
        # Add reverse nickname lookup
        for canonical, nicknames in self.NICKNAME_MAP.items():
            if first in nicknames:
                if last:
                    variations.add(f"{canonical} {last}")
                    if middle:
                        variations.add(f"{canonical} {middle[0]} {last}")
                        variations.add(f"{canonical} {middle} {last}")
        
        # Add initials-only version
        if first and last:
            variations.add(f"{first[0]} {last}")
            variations.add(f"{first[0]}. {last}")
            if middle:
                variations.add(f"{first[0]} {middle[0]} {last}")
                variations.add(f"{first[0]}. {middle[0]}. {last}")
        
        # Clean up variations
        cleaned_variations = set()
        for var in variations:
            cleaned = re.sub(r'\s+', ' ', var.strip())
            if cleaned:
                cleaned_variations.add(cleaned)
        
        return cleaned_variations
    
    def calculate_similarity_scores(self, name1: str, name2: str) -> Dict[str, float]:
        """
        Calculate multiple similarity scores between two names
        
        Args:
            name1 (str): First name
            name2 (str): Second name
            
        Returns:
            Dict[str, float]: Dictionary of similarity scores
        """
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if not norm1 or not norm2:
            return {}
        
        scores = {}
        
        # Fuzzy string matching scores
        scores['token_sort_ratio'] = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        scores['token_set_ratio'] = fuzz.token_set_ratio(norm1, norm2) / 100.0
        scores['partial_ratio'] = fuzz.partial_ratio(norm1, norm2) / 100.0
        scores['ratio'] = fuzz.ratio(norm1, norm2) / 100.0
        
        # Phonetic matching
        try:
            scores['soundex'] = 1.0 if jellyfish.soundex(norm1) == jellyfish.soundex(norm2) else 0.0
            scores['metaphone'] = 1.0 if jellyfish.metaphone(norm1) == jellyfish.metaphone(norm2) else 0.0
            scores['jaro'] = jellyfish.jaro_similarity(norm1, norm2)
            scores['jaro_winkler'] = jellyfish.jaro_winkler_similarity(norm1, norm2)
        except:
            # Handle cases where phonetic algorithms fail
            scores['soundex'] = 0.0
            scores['metaphone'] = 0.0
            scores['jaro'] = 0.0
            scores['jaro_winkler'] = 0.0
        
        # Calculate composite score
        scores['composite'] = (
            scores['token_sort_ratio'] * 0.3 +
            scores['token_set_ratio'] * 0.25 +
            scores['jaro_winkler'] * 0.2 +
            scores['partial_ratio'] * 0.15 +
            scores['ratio'] * 0.1
        )
        
        return scores
    
    def find_best_matches(self, target_name: str, candidate_names: List[str], 
                         top_k: int = 5) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Find the best matches for a target name from a list of candidates
        
        Args:
            target_name (str): Name to match
            candidate_names (List[str]): List of candidate names
            top_k (int): Number of top matches to return
            
        Returns:
            List[Tuple[str, float, Dict[str, float]]]: List of (name, composite_score, all_scores)
        """
        if not target_name or not candidate_names:
            return []
        
        matches = []
        target_variations = self.generate_name_variations(target_name)
        
        for candidate in candidate_names:
            candidate_variations = self.generate_name_variations(candidate)
            
            # Find best score among all variation combinations
            best_score = 0.0
            best_scores_dict = {}
            
            for target_var in target_variations:
                for candidate_var in candidate_variations:
                    scores = self.calculate_similarity_scores(target_var, candidate_var)
                    if scores and scores.get('composite', 0) > best_score:
                        best_score = scores['composite']
                        best_scores_dict = scores
            
            if best_score >= self.similarity_threshold:
                matches.append((candidate, best_score, best_scores_dict))
        
        # Sort by composite score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]
    
    def is_likely_same_person(self, name1: str, name2: str, strict: bool = False) -> bool:
        """
        Determine if two names likely refer to the same person
        
        Args:
            name1 (str): First name
            name2 (str): Second name
            strict (bool): Whether to use strict matching criteria
            
        Returns:
            bool: True if names likely refer to same person
        """
        scores = self.calculate_similarity_scores(name1, name2)
        if not scores:
            return False
        
        threshold = 0.9 if strict else self.similarity_threshold
        
        # Check multiple criteria
        high_fuzzy_match = scores.get('token_sort_ratio', 0) >= threshold
        high_phonetic_match = scores.get('jaro_winkler', 0) >= threshold
        high_composite = scores.get('composite', 0) >= threshold
        
        # Also check if names are variations of each other
        variations1 = self.generate_name_variations(name1)
        variations2 = self.generate_name_variations(name2)
        
        # Normalize for comparison
        variations1_norm = {self.normalize_name(v) for v in variations1}
        variations2_norm = {self.normalize_name(v) for v in variations2}
        
        has_overlap = bool(variations1_norm & variations2_norm)
        
        return high_composite or (high_fuzzy_match and high_phonetic_match) or has_overlap
    
    def deduplicate_names(self, names: List[str]) -> List[str]:
        """
        Remove duplicate names from a list, keeping the most complete version
        
        Args:
            names (List[str]): List of names potentially containing duplicates
            
        Returns:
            List[str]: Deduplicated list of names
        """
        if not names:
            return []
        
        # Group similar names
        groups = []
        processed = set()
        
        for i, name1 in enumerate(names):
            if i in processed:
                continue
                
            group = [name1]
            processed.add(i)
            
            for j, name2 in enumerate(names[i+1:], i+1):
                if j in processed:
                    continue
                    
                if self.is_likely_same_person(name1, name2):
                    group.append(name2)
                    processed.add(j)
            
            groups.append(group)
        
        # Select best representative from each group
        result = []
        for group in groups:
            # Prefer longer, more complete names
            best = max(group, key=lambda x: (len(x), x.count(' '), x))
            result.append(best)
        
        return sorted(result)


# Example usage and testing
if __name__ == "__main__":
    matcher = EnhancedNameMatcher()
    
    # Test cases
    test_names = [
        "Dr. Michael J. Smith",
        "Mike Smith", 
        "M. Smith",
        "Smith, Michael",
        "José María García",
        "Jose Garcia",
        "François Müller",
        "Francois Mueller",
        "李明",  # Chinese name
        "Ming Li"
    ]
    
    print("Enhanced Name Matching Test Results:")
    print("=" * 50)
    
    target = "Michael Smith"
    print(f"\nFinding matches for: {target}")
    matches = matcher.find_best_matches(target, test_names)
    
    for name, score, scores in matches:
        print(f"  {name}: {score:.3f}")
        print(f"    Token sort: {scores.get('token_sort_ratio', 0):.3f}")
        print(f"    Jaro-Winkler: {scores.get('jaro_winkler', 0):.3f}")
        print(f"    Soundex match: {scores.get('soundex', 0):.3f}")
    
    print(f"\nName variations for '{target}':")
    variations = matcher.generate_name_variations(target)
    for var in sorted(variations):
        print(f"  {var}")
    
    print(f"\nDuplication test:")
    duplicates = ["Michael Smith", "Mike Smith", "M. Smith", "John Doe", "J. Doe"]
    deduped = matcher.deduplicate_names(duplicates)
    print(f"  Original: {duplicates}")
    print(f"  Deduped: {deduped}")
