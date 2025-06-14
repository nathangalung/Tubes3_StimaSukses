"""Search timing utility"""

import time
from typing import Optional

class SearchTimer:
    """Search timer utility"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all timers"""
        self.total_start_time = None
        self.exact_start_time = None
        self.fuzzy_start_time = None
        self.total_time = 0.0
        self.exact_time = 0.0
        self.fuzzy_time = 0.0
        self.algorithm_used = ""
        self.cvs_processed = 0
    
    def start_total_search(self):
        """Start total search timer"""
        self.total_start_time = time.time()
    
    def stop_total_search(self):
        """Stop total search timer"""
        if self.total_start_time:
            self.total_time = time.time() - self.total_start_time
    
    def start_exact_search(self, algorithm: str, cv_count: int):
        """Start exact search timer"""
        self.exact_start_time = time.time()
        self.algorithm_used = algorithm
        self.cvs_processed = cv_count
    
    def stop_exact_search(self):
        """Stop exact search timer"""
        if self.exact_start_time:
            self.exact_time = time.time() - self.exact_start_time
    
    def start_fuzzy_search(self, keyword_count: int):
        """Start fuzzy search timer"""
        self.fuzzy_start_time = time.time()
    
    def stop_fuzzy_search(self):
        """Stop fuzzy search timer"""
        if self.fuzzy_start_time:
            self.fuzzy_time = time.time() - self.fuzzy_start_time
    
    def get_search_summary(self) -> str:
        """Get timing summary"""
        lines = [
            f"⏱️ Search Performance Summary:",
            f"  • Total Time: {self.total_time:.3f}s",
            f"  • Algorithm: {self.algorithm_used}",
            f"  • CVs Processed: {self.cvs_processed}"
        ]
        
        if self.exact_time > 0:
            lines.append(f"  • Exact Search: {self.exact_time:.3f}s")
        
        if self.fuzzy_time > 0:
            lines.append(f"  • Fuzzy Search: {self.fuzzy_time:.3f}s")
        
        return "\n".join(lines)