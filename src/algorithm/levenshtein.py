"""Levenshtein distance for fuzzy matching"""

from typing import List, Dict, Tuple
import re

class LevenshteinMatcher:
    """Levenshtein distance fuzzy matcher"""
    
    def __init__(self):
        self.max_distance = 3
        self.min_word_length = 3
    
    def distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        if len(s1) < len(s2):
            return self.distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        # Create distance matrix
        previous_row = list(range(len(s2) + 1))
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                # Cost of operations
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    def similarity_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio (0-1)"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        dist = self.distance(s1, s2)
        return 1.0 - (dist / max_len)
    
    def fuzzy_search(self, text: str, pattern: str, threshold: float = 0.7) -> List[int]:
        """Find fuzzy matches in text"""
        if len(pattern) < self.min_word_length:
            return []
        
        matches = []
        words = self._extract_words(text)
        
        for word, start_pos in words:
            if len(word) >= self.min_word_length:
                similarity = self.similarity_ratio(word.lower(), pattern.lower())
                
                if similarity >= threshold:
                    matches.append(start_pos)
        
        return matches
    
    def fuzzy_search_multiple(self, text: str, patterns: List[str], 
                            threshold: float = 0.7) -> Dict[str, List[int]]:
        """Search multiple patterns with fuzzy matching"""
        results = {}
        
        for pattern in patterns:
            matches = self.fuzzy_search(text, pattern, threshold)
            if matches:
                results[pattern.lower()] = matches
        
        return results
    
    def find_best_matches(self, text: str, pattern: str, 
                         max_matches: int = 10) -> List[Tuple[str, int, float]]:
        """Find best fuzzy matches with scores"""
        if len(pattern) < self.min_word_length:
            return []
        
        matches = []
        words = self._extract_words(text)
        
        for word, start_pos in words:
            if len(word) >= self.min_word_length:
                similarity = self.similarity_ratio(word.lower(), pattern.lower())
                
                if similarity > 0.5:  # Minimum threshold
                    matches.append((word, start_pos, similarity))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[2], reverse=True)
        
        return matches[:max_matches]
    
    def _extract_words(self, text: str) -> List[Tuple[str, int]]:
        """Extract words with positions"""
        words = []
        
        # Find word boundaries
        for match in re.finditer(r'\b\w+\b', text):
            word = match.group()
            start_pos = match.start()
            words.append((word, start_pos))
        
        return words
    
    def get_suggestions(self, text: str, pattern: str, 
                       max_suggestions: int = 5) -> List[str]:
        """Get spelling suggestions"""
        best_matches = self.find_best_matches(text, pattern, max_suggestions * 2)
        
        # Remove duplicates and low scores
        seen = set()
        suggestions = []
        
        for word, _, score in best_matches:
            word_lower = word.lower()
            if word_lower not in seen and score > 0.6:
                seen.add(word_lower)
                suggestions.append(word)
                
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions

def test_levenshtein_distance():
    """Test Levenshtein implementation"""
    matcher = LevenshteinMatcher()
    
    # Distance tests
    test_cases = [
        ("kitten", "sitting", 3),
        ("python", "python", 0),
        ("hello", "helo", 1),
        ("java", "javascript", 6),
        ("", "test", 4),
        ("same", "same", 0)
    ]
    
    print("=== LEVENSHTEIN DISTANCE TEST ===")
    all_passed = True
    
    for s1, s2, expected in test_cases:
        result = matcher.distance(s1, s2)
        print(f"'{s1}' -> '{s2}': {result} (expected: {expected})")
        
        if result == expected:
            print("✅ CORRECT")
        else:
            print("❌ INCORRECT")
            all_passed = False
        
        print("-" * 30)
    
    # Fuzzy search test
    print("\n=== FUZZY SEARCH TEST ===")
    text = "Python programming with Java and JavaScript development"
    patterns = ["Pyhton", "Jav", "development"]
    
    results = matcher.fuzzy_search_multiple(text, patterns, threshold=0.6)
    print(f"Text: {text}")
    print(f"Patterns: {patterns}")
    print(f"Results: {results}")
    
    return all_passed

if __name__ == "__main__":
    success = test_levenshtein_distance()
    if success:
        print("🎉 Levenshtein implementation is CORRECT!")
    else:
        print("❌ Levenshtein needs fixes!")