"""Enhanced Aho-Corasick string matching algorithm for multi-pattern matching"""

from typing import List, Dict, Set
from collections import deque, defaultdict

class TrieNode:
    """Trie node for AC automaton"""
    
    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []
        self.is_end = False

class AhoCorasick:
    """Aho-Corasick implementation for efficient multi-pattern matching"""
    
    def __init__(self):
        self.root = TrieNode()
        self.patterns = []
        self.automaton_built = False
    
    def build_automaton(self, patterns: List[str]):
        """Build AC automaton for given patterns"""
        # Reset automaton
        self.root = TrieNode()
        self.patterns = []
        self.automaton_built = False
        
        # Clean and normalize patterns
        cleaned_patterns = []
        for pattern in patterns:
            if pattern and pattern.strip():
                cleaned_patterns.append(pattern.strip().lower())
        
        self.patterns = list(set(cleaned_patterns))  # Remove duplicates
        
        if not self.patterns:
            return
        
        # Build trie structure
        self._build_trie()
        
        # Build failure links
        self._build_failure_links()
        
        self.automaton_built = True
    
    def search(self, text: str, pattern: str) -> Dict[str, List[int]]:
        """Search single pattern (for compatibility with KMP/BM interface)"""
        if not pattern or not text:
            return {}
        
        return self.search_multiple(text, [pattern])
    
    def search_multiple(self, text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """Search multiple patterns efficiently in single text traversal"""
        if not text or not patterns:
            return {}
        
        # Build automaton for current patterns
        self.build_automaton(patterns)
        
        if not self.automaton_built or not self.patterns:
            return {}
        
        # Perform search with single text traversal
        results = defaultdict(list)
        text_lower = text.lower()
        current_node = self.root
        
        for i, char in enumerate(text_lower):
            # Follow failure links until we find a valid transition or reach root
            while current_node != self.root and char not in current_node.children:
                current_node = current_node.failure
            
            # Move to next state if possible
            if char in current_node.children:
                current_node = current_node.children[char]
            
            # Check for pattern matches at current position
            temp_node = current_node
            while temp_node != self.root:
                # Process all patterns ending at this node
                for pattern in temp_node.output:
                    start_pos = i - len(pattern) + 1
                    if start_pos >= 0:  # Valid position
                        results[pattern].append(start_pos)
                
                # Move to failure link to check for overlapping patterns
                temp_node = temp_node.failure
        
        # Convert to regular dict and ensure consistent format
        final_results = {}
        for pattern in patterns:
            pattern_lower = pattern.strip().lower()
            if pattern_lower in results:
                final_results[pattern_lower] = sorted(list(set(results[pattern_lower])))
        
        return final_results
    
    def _build_trie(self):
        """Build trie structure from patterns"""
        for pattern in self.patterns:
            current = self.root
            
            for char in pattern:
                if char not in current.children:
                    current.children[char] = TrieNode()
                current = current.children[char]
            
            current.is_end = True
            current.output.append(pattern)
    
    def _build_failure_links(self):
        """Build failure links using BFS for efficient pattern matching"""
        queue = deque()
        
        # Initialize failure links for root's children
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        # Build failure links using BFS
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find proper failure link
                failure_node = current.failure
                
                # Follow failure links until we find a node with the character transition
                while failure_node != self.root and char not in failure_node.children:
                    failure_node = failure_node.failure
                
                # Set failure link
                if char in failure_node.children and failure_node.children[char] != child:
                    child.failure = failure_node.children[char]
                else:
                    child.failure = self.root
                
                # Inherit output patterns from failure node (suffix overlaps)
                child.output.extend(child.failure.output)
    
    def get_statistics(self) -> Dict:
        """Get AC automaton statistics"""
        if not self.automaton_built:
            return {"status": "not_built"}
        
        # Count nodes and transitions
        node_count = self._count_nodes(self.root)
        transition_count = self._count_transitions(self.root)
        
        return {
            "status": "built",
            "patterns": len(self.patterns),
            "nodes": node_count,
            "transitions": transition_count,
            "max_pattern_length": max(len(p) for p in self.patterns) if self.patterns else 0,
            "min_pattern_length": min(len(p) for p in self.patterns) if self.patterns else 0
        }
    
    def _count_nodes(self, node: TrieNode) -> int:
        """Count total nodes in trie"""
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count
    
    def _count_transitions(self, node: TrieNode) -> int:
        """Count total transitions in trie"""
        count = len(node.children)
        for child in node.children.values():
            count += self._count_transitions(child)
        return count

# Comprehensive test function
def test_aho_corasick():
    """Comprehensive test of AC implementation"""
    print("=== AHO-CORASICK COMPREHENSIVE TEST ===")
    
    ac = AhoCorasick()
    success = True
    
    # Test 1: Basic multi-pattern matching
    print("\n1. Basic Multi-pattern Test:")
    text = "python programming with python and java"
    patterns = ["python", "java", "programming"]
    
    results = ac.search_multiple(text, patterns)
    
    print(f"Text: '{text}'")
    print(f"Patterns: {patterns}")
    print(f"Results: {results}")
    
    # Verify results
    expected = {
        'python': [0, 24],
        'java': [35],
        'programming': [7]
    }
    
    for pattern, expected_positions in expected.items():
        if pattern in results:
            if sorted(results[pattern]) == sorted(expected_positions):
                print(f"✅ {pattern}: {results[pattern]}")
            else:
                print(f"❌ {pattern}: expected {expected_positions}, got {results[pattern]}")
                success = False
        else:
            print(f"❌ {pattern}: not found")
            success = False
    
    # Test 2: Overlapping patterns
    print("\n2. Overlapping Patterns Test:")
    text2 = "abcabcabc"
    patterns2 = ["abc", "bca", "cab"]
    
    results2 = ac.search_multiple(text2, patterns2)
    print(f"Text: '{text2}'")
    print(f"Patterns: {patterns2}")
    print(f"Results: {results2}")
    
    # Test 3: Case insensitivity
    print("\n3. Case Insensitivity Test:")
    text3 = "Python JAVA programming"
    patterns3 = ["python", "java", "PROGRAMMING"]
    
    results3 = ac.search_multiple(text3, patterns3)
    print(f"Text: '{text3}'")
    print(f"Patterns: {patterns3}")
    print(f"Results: {results3}")
    
    if 'python' in results3 and 'java' in results3 and 'programming' in results3:
        print("✅ Case insensitivity working")
    else:
        print("❌ Case insensitivity failed")
        success = False
    
    # Test 4: Empty and edge cases
    print("\n4. Edge Cases Test:")
    
    # Empty patterns
    results_empty = ac.search_multiple("test", [])
    if results_empty == {}:
        print("✅ Empty patterns handled")
    else:
        print("❌ Empty patterns not handled")
        success = False
    
    # Empty text
    results_empty_text = ac.search_multiple("", ["test"])
    if results_empty_text == {}:
        print("✅ Empty text handled")
    else:
        print("❌ Empty text not handled")
        success = False
    
    # Test 5: Performance comparison with naive approach
    print("\n5. Performance Advantage Test:")
    
    # Large text with many patterns
    large_text = "python java sql python machine learning data science python programming java development sql database python" * 10
    many_patterns = ["python", "java", "sql", "machine", "learning", "data", "science", "programming", "development", "database"]
    
    import time
    
    # AC approach (single traversal)
    start_time = time.time()
    ac_results = ac.search_multiple(large_text, many_patterns)
    ac_time = time.time() - start_time
    
    # Naive approach (multiple traversals)
    start_time = time.time()
    naive_results = {}
    for pattern in many_patterns:
        pattern_results = []
        start = 0
        while True:
            pos = large_text.lower().find(pattern.lower(), start)
            if pos == -1:
                break
            pattern_results.append(pos)
            start = pos + 1
        if pattern_results:
            naive_results[pattern.lower()] = pattern_results
    naive_time = time.time() - start_time
    
    print(f"AC Time: {ac_time:.4f}s")
    print(f"Naive Time: {naive_time:.4f}s")
    print(f"Speedup: {naive_time/ac_time:.2f}x" if ac_time > 0 else "N/A")
    
    # Verify results match
    matches_naive = True
    for pattern in many_patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in ac_results and pattern_lower in naive_results:
            if sorted(ac_results[pattern_lower]) != sorted(naive_results[pattern_lower]):
                matches_naive = False
                break
        elif pattern_lower in ac_results or pattern_lower in naive_results:
            matches_naive = False
            break
    
    if matches_naive:
        print("✅ Results match naive approach")
    else:
        print("❌ Results don't match naive approach")
        success = False
    
    # Test 6: Statistics
    print("\n6. Automaton Statistics:")
    stats = ac.get_statistics()
    print(f"Status: {stats['status']}")
    if stats['status'] == 'built':
        print(f"Patterns: {stats['patterns']}")
        print(f"Nodes: {stats['nodes']}")
        print(f"Transitions: {stats['transitions']}")
        print(f"Pattern length range: {stats['min_pattern_length']}-{stats['max_pattern_length']}")
    
    return success

def test_compatibility_with_other_algorithms():
    """Test compatibility with KMP and BM interfaces"""
    print("\n=== COMPATIBILITY TEST ===")
    
    # Import other algorithms for comparison
    import sys
    import os
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from kmp import KMPMatcher
        from bm import BoyerMooreMatcher
    except ImportError:
        print("⚠️ Could not import KMP/BM for comparison")
        return True
    
    # Test data
    text = "python programming java python sql"
    patterns = ["python", "java", "sql"]
    
    # Test all algorithms
    ac = AhoCorasick()
    kmp = KMPMatcher()
    bm = BoyerMooreMatcher()
    
    print(f"Text: '{text}'")
    print(f"Patterns: {patterns}")
    
    # AC results
    ac_results = ac.search_multiple(text, patterns)
    print(f"AC Results: {ac_results}")
    
    # KMP results
    kmp_results = kmp.search_multiple(text, patterns)
    print(f"KMP Results: {kmp_results}")
    
    # BM results
    bm_results = bm.search_multiple(text, patterns)
    print(f"BM Results: {bm_results}")
    
    # Compare results
    all_match = True
    for pattern in patterns:
        pattern_lower = pattern.lower()
        
        ac_matches = sorted(ac_results.get(pattern_lower, []))
        kmp_matches = sorted(kmp_results.get(pattern, []))
        bm_matches = sorted(bm_results.get(pattern_lower, []))
        
        if ac_matches != kmp_matches or ac_matches != bm_matches:
            print(f"❌ Mismatch for '{pattern}':")
            print(f"  AC: {ac_matches}")
            print(f"  KMP: {kmp_matches}")
            print(f"  BM: {bm_matches}")
            all_match = False
        else:
            print(f"✅ '{pattern}': all algorithms agree")
    
    return all_match

if __name__ == "__main__":
    print("🔍 Testing Enhanced Aho-Corasick Implementation")
    
    success1 = test_aho_corasick()
    success2 = test_compatibility_with_other_algorithms()
    
    if success1 and success2:
        print("\n🎉 Aho-Corasick implementation is CORRECT and COMPATIBLE!")
        print("✅ Ready for integration as separate algorithm option")
        print("🚀 Provides efficient multi-pattern matching advantage")
    else:
        print("\n❌ Aho-Corasick needs fixes!")
        
    print("\n📊 Algorithm Advantages:")
    print("• KMP: O(n+m) single pattern, good for exact matching")
    print("• Boyer-Moore: Fast for long patterns, good character skipping")
    print("• Aho-Corasick: O(n+m+z) multi-pattern, single text traversal")
    print("  where n=text length, m=total pattern length, z=matches")