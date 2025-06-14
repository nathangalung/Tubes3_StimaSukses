"""Boyer-Moore string matching algorithm"""

from typing import List, Dict

class BoyerMooreMatcher:
    """Boyer-Moore string matching implementation"""
    
    def __init__(self):
        pass
    
    def search(self, text: str, pattern: str) -> List[int]:
        """Search pattern in text"""
        if not pattern or not text:
            return []
        
        # Build bad character table
        bad_char = self._build_bad_character_table(pattern)
        
        # Search
        matches = []
        shift = 0
        
        while shift <= len(text) - len(pattern):
            j = len(pattern) - 1
            
            # Compare from right to left
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1
            
            if j < 0:
                # Pattern found
                matches.append(shift)
                # Move to next possible position
                if shift + len(pattern) < len(text):
                    shift += len(pattern) - bad_char.get(text[shift + len(pattern)], -1)
                else:
                    shift += 1
            else:
                # Mismatch, use bad character rule
                bad_char_shift = max(1, j - bad_char.get(text[shift + j], -1))
                shift += bad_char_shift
        
        return matches
    
    def search_multiple(self, text: str, patterns: List[str]) -> Dict[str, List[int]]:
        """Search multiple patterns"""
        results = {}
        for pattern in patterns:
            matches = self.search(text, pattern)
            if matches:
                results[pattern.lower()] = matches
        return results
    
    def _build_bad_character_table(self, pattern: str) -> Dict[str, int]:
        """Build bad character table"""
        bad_char = {}
        
        for i in range(len(pattern)):
            bad_char[pattern[i]] = i
        
        return bad_char

def test_boyer_moore_consistency():
    """Test BM against naive implementation"""
    
    def naive_search(text, pattern):
        """Naive implementation for comparison"""
        results = []
        for i in range(len(text) - len(pattern) + 1):
            if text[i:i+len(pattern)] == pattern:
                results.append(i)
        return results
    
    # Test cases
    test_cases = [
        ("python java sql python", "python"),
        ("aaaa", "aa"),
        ("hello world hello", "hello"),
        ("abcdefg", "xyz"),
        ("SQL database SQL queries SQL", "SQL"),
    ]
    
    bm = BoyerMooreMatcher()
    
    print("=== BOYER-MOORE CONSISTENCY TEST ===")
    all_passed = True
    
    for text, pattern in test_cases:
        bm_result = bm.search(text, pattern)
        naive_result = naive_search(text, pattern)
        
        print(f"Text: '{text}'")
        print(f"Pattern: '{pattern}'")
        print(f"BM Result: {bm_result}")
        print(f"Naive Result: {naive_result}")
        
        if bm_result == naive_result:
            print("✅ CONSISTENT")
        else:
            print("❌ INCONSISTENT!")
            all_passed = False
        
        print("-" * 40)
    
    return all_passed

if __name__ == "__main__":
    success = test_boyer_moore_consistency()
    if success:
        print("🎉 Boyer-Moore implementation is CORRECT!")
    else:
        print("❌ Boyer-Moore needs more fixes!")