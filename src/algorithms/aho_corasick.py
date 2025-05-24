class AhoCorasick:
    def __init__(self, keywords):
        """Initializes the Aho-Corasick automaton."""
        self.goto = [{}]  # Adjacency list for trie
        self.output = [[] for _ in range(1)]  # Output for each node
        self.failure = [0]  # Failure links
        self._build_trie(keywords)
        self._build_failure_links()

    def _build_trie(self, keywords):
        """Builds the trie from keywords."""
        for keyword_idx, keyword in enumerate(keywords):
            node = 0
            for char in keyword:
                if char not in self.goto[node]:
                    self.goto[node][char] = len(self.goto)
                    self.goto.append({})
                    self.output.append([])
                    self.failure.append(0)
                node = self.goto[node][char]
            self.output[node].append(keyword) # Store keyword at end

    def _build_failure_links(self):
        """Builds failure links using BFS."""
        queue = []
        for char_code in range(256): # Assuming ASCII characters
            char = chr(char_code)
            if char in self.goto[0]:
                node = self.goto[0][char]
                queue.append(node)
                self.failure[node] = 0 # Root's children fail to root

        head = 0
        while head < len(queue):
            current_node = queue[head]
            head += 1

            for char_code in range(256):
                char = chr(char_code)
                if char in self.goto[current_node]:
                    next_node = self.goto[current_node][char]
                    queue.append(next_node)
                    
                    fail_node = self.failure[current_node]
                    while char not in self.goto[fail_node] and fail_node != 0:
                        fail_node = self.failure[fail_node]
                    
                    if char in self.goto[fail_node]:
                        self.failure[next_node] = self.goto[fail_node][char]
                    else:
                        self.failure[next_node] = 0 # Default to root
                    
                    # Merge output with failure link's output
                    self.output[next_node].extend(self.output[self.failure[next_node]])


    def search(self, text):
        """Searches for keywords in text."""
        current_node = 0
        results = {} # Keyword: [positions]

        for i, char in enumerate(text):
            while char not in self.goto[current_node] and current_node != 0:
                current_node = self.failure[current_node]
            
            if char in self.goto[current_node]:
                current_node = self.goto[current_node][char]
            else:
                # If char not in root's children, stay at root
                current_node = 0 
            
            if self.output[current_node]:
                for keyword in self.output[current_node]:
                    if keyword not in results:
                        results[keyword] = []
                    # Position is end of keyword
                    results[keyword].append(i - len(keyword) + 1)
        return results

# Example usage:
keywords = ["he", "she", "his", "hers"]
text = "ushers"
ac = AhoCorasick(keywords)
print(ac.search(text))
# Expected: {'she': [2], 'he': [3], 'hers': [4]}