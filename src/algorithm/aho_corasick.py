"""Aho-Corasick string matching algorithm"""

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
    """ Aho-Corasick implementation"""
    
    def __init__(self):
        self.root = TrieNode()
        self.patterns = []
    
    def build_automaton(self, patterns: List[str]):
        """Build AC automaton"""
        self.patterns = [p.lower() for p in patterns if p.strip()]
        
        if not self.patterns:
            return
        
        # Build trie
        self._build_trie()
        
        # Build failure links
        self._build_failure_links()
    
    def search_multiple(self, text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """Search multiple patterns"""
        if not text or not patterns:
            return {}
        
        # Build automaton
        self.build_automaton(patterns)
        
        if not self.patterns:
            return {}
        
        # Search
        results = defaultdict(list)
        text_lower = text.lower()
        current_node = self.root
        
        for i, char in enumerate(text_lower):
            # Follow failure links
            while current_node != self.root and char not in current_node.children:
                current_node = current_node.failure
            
            # Move to next state
            if char in current_node.children:
                current_node = current_node.children[char]
            
            # Check for matches
            temp_node = current_node
            while temp_node != self.root:
                for pattern in temp_node.output:
                    start_pos = i - len(pattern) + 1
                    results[pattern].append(start_pos)
                temp_node = temp_node.failure
        
        return dict(results)
    
    def _build_trie(self):
        """Build trie structure"""
        for pattern in self.patterns:
            current = self.root
            
            for char in pattern:
                if char not in current.children:
                    current.children[char] = TrieNode()
                current = current.children[char]
            
            current.is_end = True
            current.output.append(pattern)
    
    def _build_failure_links(self):
        """Build failure links using BFS"""
        queue = deque()
        
        # Initialize root children
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        # BFS to build failure links
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link
                failure_node = current.failure
                while failure_node != self.root and char not in failure_node.children:
                    failure_node = failure_node.failure
                
                if char in failure_node.children and failure_node.children[char] != child:
                    child.failure = failure_node.children[char]
                else:
                    child.failure = self.root
                
                # Copy output from failure node
                child.output.extend(child.failure.output)

# Test function
def test_aho_corasick():
    """Test AC implementation"""
    ac = AhoCorasick()
    
    # Test case 1: Multiple patterns
    text = "python programming with python and java"
    patterns = ["python", "java", "programming"]
    
    results = ac.search_multiple(text, patterns)
    
    print("=== AHO-CORASICK TEST ===")
    print(f"Text: '{text}'")
    print(f"Patterns: {patterns}")
    print(f"Results: {results}")
    
    # Verify results
    expected = {
        'python': [0, 24],
        'java': [35],
        'programming': [7]
    }
    
    success = True
    for pattern, expected_positions in expected.items():
        if pattern in results:
            if results[pattern] != expected_positions:
                print(f"❌ {pattern}: expected {expected_positions}, got {results[pattern]}")
                success = False
            else:
                print(f"✅ {pattern}: {results[pattern]}")
        else:
            print(f"❌ {pattern}: not found")
            success = False
    
    return success

if __name__ == "__main__":
    success = test_aho_corasick()
    if success:
        print("🎉 Aho-Corasick implementation is CORRECT!")
    else:
        print("❌ Aho-Corasick needs fixes!")