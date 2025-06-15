"""CV search controller"""
from typing import List, Tuple, Dict
import time
from database.models import SearchResult
from database.repo import ResumeRepository
from utils.pdf_extractor import PDFExtractor
from utils.timer import SearchTimer
from algorithm.kmp import KMPMatcher
from algorithm.bm import BoyerMooreMatcher
from algorithm.aho_corasick import AhoCorasick
from algorithm.levenshtein import LevenshteinMatcher

class SearchController:
    """CV search controller"""
    
    def __init__(self):
        # Initialize components
        self.repo = ResumeRepository()
        self.pdf_extractor = PDFExtractor()
        self.timer = SearchTimer()
        
        # Algorithm matchers
        self.kmp_matcher = KMPMatcher()
        self.bm_matcher = BoyerMooreMatcher()
        self.aho_corasick = AhoCorasick()
        self.levenshtein_matcher = LevenshteinMatcher()
        
        # Configuration
        self.progress_callback = None
        self.max_cvs_to_process = 100
        self.batch_size = 10
        
        # Performance tracking
        self.algorithm_stats = {
            'KMP': {'total_time': 0, 'searches': 0},
            'BM': {'total_time': 0, 'searches': 0},
            'AC': {'total_time': 0, 'searches': 0},
            'LEVENSHTEIN': {'total_time': 0, 'searches': 0}
        }

    def set_progress_callback(self, callback):
        """Set progress callback"""
        self.progress_callback = callback

    def search_cvs(self, keywords: List[str], algorithm: str = 'KMP', 
                   top_n: int = 10, fuzzy_threshold: float = 0.7) -> Tuple[List[SearchResult], str]:
        """Main search function"""
        
        print(f"🔍 Starting search: {keywords}, {algorithm}")
        
        # Initialize timer
        self.timer.reset()
        
        # Get resumes
        all_resumes = self.repo.get_all_resumes()
        if not all_resumes:
            return [], "No CVs found"
        
        # Limit for performance
        resumes = all_resumes[:self.max_cvs_to_process]
        print(f"📄 Processing {len(resumes)} resumes")
        
        # Debug sample paths
        for i, resume in enumerate(resumes[:3]):
            print(f"   {i+1}.{resume.id}: {resume.file_path}")
        
        # Execute search
        if algorithm.upper() == 'LEVENSHTEIN':
            results = self._execute_fuzzy_search(resumes, keywords, fuzzy_threshold)
        else:
            results = self._execute_exact_search(resumes, keywords, algorithm, fuzzy_threshold, top_n)
        
        # Calculate and sort
        results = self._calculate_relevance_scores(results, keywords)
        results.sort(key=lambda x: (x.relevance_score, x.total_matches), reverse=True)
        
        # Return top results
        top_results = results[:top_n]
        timing_summary = self._generate_timing_summary()
        
        print(f"🎯 Completed: {len(top_results)} results")
        
        # Show statistics
        stats = self.pdf_extractor.get_extraction_stats()
        print(f"📊 PDF: {stats['cached_files']} success, {stats['failed_files']} failed")
        
        return top_results, timing_summary

    def _execute_exact_search(self, resumes, keywords, algorithm, fuzzy_threshold, top_n):
        """Execute exact search with fallback"""
        
        # Start exact search
        self.timer.start_exact_search(algorithm, len(resumes))
        start_time = time.time()
        
        # Choose algorithm
        if algorithm.upper() == 'AC':
            exact_results = self._aho_corasick_search(resumes, keywords)
        else:
            exact_results = self._batched_exact_search(resumes, keywords, algorithm)
        
        # Update statistics
        exact_time = time.time() - start_time
        self.algorithm_stats[algorithm.upper()]['total_time'] += exact_time
        self.algorithm_stats[algorithm.upper()]['searches'] += 1
        
        self.timer.stop_exact_search()
        print(f"✅ Exact: {len(exact_results)} matches in {exact_time:.3f}s")
        
        # Fuzzy fallback if needed
        unfound_keywords = self._get_unfound_keywords(exact_results, keywords)
        fuzzy_results = []
        
        if unfound_keywords and len(exact_results) < top_n:
            print(f"🔍 Fuzzy fallback: {unfound_keywords}")
            self.timer.start_fuzzy_search(len(unfound_keywords))
            
            start_time = time.time()
            fuzzy_resumes = resumes[:50]
            fuzzy_results = self._fuzzy_search(fuzzy_resumes, unfound_keywords, fuzzy_threshold)
            
            fuzzy_time = time.time() - start_time
            self.algorithm_stats['LEVENSHTEIN']['total_time'] += fuzzy_time
            self.algorithm_stats['LEVENSHTEIN']['searches'] += 1
            
            self.timer.stop_fuzzy_search()
            print(f"🔀 Fuzzy: {len(fuzzy_results)} matches in {fuzzy_time:.3f}s")
        
        return exact_results + fuzzy_results

    def _batched_exact_search(self, resumes, keywords, algorithm):
        """Exact search with batch processing"""
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        total_batches = (len(resumes) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(resumes))
            batch_resumes = resumes[start_idx:end_idx]
            
            if self.progress_callback:
                progress = (batch_idx + 1) / total_batches * 100
                self.progress_callback(f"{algorithm}: batch {batch_idx + 1}/{total_batches} ({progress:.0f}%)")
            
            for resume in batch_resumes:
                try:
                    cv_text = self.pdf_extractor.extract_text(resume.file_path)
                    if not cv_text or len(cv_text.strip()) < 50:
                        continue
                    
                    successful_extractions += 1
                    sample_text = cv_text[:100].replace('\n', ' ')
                    print(f"📝 Sample: {sample_text}...")
                    
                    # Search using algorithm
                    if algorithm.upper() == 'KMP':
                        matches = self._kmp_search_keywords(cv_text, keywords)
                    elif algorithm.upper() == 'BM':
                        matches = self._bm_search_keywords(cv_text, keywords)
                    else:
                        continue
                    
                    # Process matches
                    if matches:
                        keyword_matches = {}
                        total_matches = 0
                        matched_keywords = []
                        
                        for keyword, count in matches.items():
                            if count > 0:
                                keyword_matches[keyword] = count
                                total_matches += count
                                matched_keywords.append(keyword)
                                print(f"✅ Found '{keyword}' {count}x in {resume.id}")
                        
                        if total_matches > 0:
                            result = SearchResult(
                                resume=resume,
                                keyword_matches=keyword_matches,
                                total_matches=total_matches,
                                matched_keywords=matched_keywords
                            )
                            result.algorithm_used = algorithm.upper()
                            results.append(result)
                            
                except Exception as e:
                    failed_extractions += 1
                    print(f"⚠️ Error: {resume.id}: {e}")
                    continue
        
        print(f"📊 Extraction: {successful_extractions} success, {failed_extractions} failed")
        return results

    def _kmp_search_keywords(self, text, keywords):
        """Search using KMP - fixed to handle dictionary return"""
        matches = {}
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # KMP returns {pattern: [positions]} - extract positions correctly
            result_dict = self.kmp_matcher.search(text_lower, keyword_lower)
            
            if result_dict and keyword_lower in result_dict:
                positions = result_dict[keyword_lower]
                matches[keyword] = len(positions)
            else:
                matches[keyword] = 0
        
        return matches

    def _bm_search_keywords(self, text, keywords):
        """Search using Boyer-Moore"""
        matches = {}
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # BM returns [positions] directly
            positions = self.bm_matcher.search(text_lower, keyword_lower)
            matches[keyword] = len(positions)
        
        return matches

    def _aho_corasick_search(self, resumes, keywords):
        """Aho-Corasick search implementation"""
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        # Build automaton once for all keywords
        self.aho_corasick.build_automaton(keywords)
        
        for resume in resumes:
            try:
                cv_text = self.pdf_extractor.extract_text(resume.file_path)
                if not cv_text or len(cv_text.strip()) < 50:
                    continue
                
                successful_extractions += 1
                
                # Search using AC
                matches = self.aho_corasick.search_multiple(cv_text.lower(), keywords)
                
                if matches:
                    keyword_matches = {}
                    total_matches = 0
                    matched_keywords = []
                    
                    for keyword, positions in matches.items():
                        count = len(positions)
                        if count > 0:
                            keyword_matches[keyword] = count
                            total_matches += count
                            matched_keywords.append(keyword)
                    
                    if total_matches > 0:
                        result = SearchResult(
                            resume=resume,
                            keyword_matches=keyword_matches,
                            total_matches=total_matches,
                            matched_keywords=matched_keywords
                        )
                        result.algorithm_used = 'AC'
                        results.append(result)
                        
            except Exception as e:
                failed_extractions += 1
                print(f"⚠️ Error: {resume.id}: {e}")
                continue
        
        return results

    def _execute_fuzzy_search(self, resumes, keywords, fuzzy_threshold):
        """Execute fuzzy search only"""
        self.timer.start_fuzzy_search(len(keywords))
        start_time = time.time()
        
        results = self._fuzzy_search(resumes, keywords, fuzzy_threshold)
        
        fuzzy_time = time.time() - start_time
        self.algorithm_stats['LEVENSHTEIN']['total_time'] += fuzzy_time
        self.algorithm_stats['LEVENSHTEIN']['searches'] += 1
        
        self.timer.stop_fuzzy_search()
        print(f"🔀 Fuzzy: {len(results)} matches in {fuzzy_time:.3f}s")
        
        return results

    def _fuzzy_search(self, resumes, keywords, threshold):
        """Fuzzy search using Levenshtein Distance"""
        results = []
        
        for resume in resumes:
            try:
                cv_text = self.pdf_extractor.extract_text(resume.file_path)
                if not cv_text or len(cv_text.strip()) < 50:
                    continue
                
                matches = self.levenshtein_matcher.fuzzy_search(cv_text, keywords, threshold)
                
                if matches:
                    keyword_matches = {}
                    total_matches = 0
                    matched_keywords = []
                    
                    for keyword, data in matches.items():
                        count = data.get('count', 0)
                        if count > 0:
                            keyword_matches[keyword] = count
                            total_matches += count
                            matched_keywords.append(keyword)
                    
                    if total_matches > 0:
                        result = SearchResult(
                            resume=resume,
                            keyword_matches=keyword_matches,
                            total_matches=total_matches,
                            matched_keywords=matched_keywords
                        )
                        result.algorithm_used = 'LEVENSHTEIN'
                        results.append(result)
                        
            except Exception as e:
                print(f"⚠️ Fuzzy error {resume.id}: {e}")
                continue
        
        return results

    def _get_unfound_keywords(self, results, original_keywords):
        """Get keywords not found in exact search"""
        found_keywords = set()
        
        for result in results:
            found_keywords.update(result.matched_keywords)
        
        unfound = [kw for kw in original_keywords if kw not in found_keywords]
        return unfound

    def _calculate_relevance_scores(self, results, keywords):
        """Calculate relevance scores"""
        for result in results:
            # Base score from matches
            base_score = result.total_matches
            
            # Keyword coverage bonus
            coverage_ratio = len(result.matched_keywords) / len(keywords)
            coverage_bonus = coverage_ratio * 20
            
            # Algorithm bonus
            algo_bonus = 10 if result.algorithm_used in ['KMP', 'BM'] else 5
            
            result.relevance_score = base_score + coverage_bonus + algo_bonus
        
        return results

    def _generate_timing_summary(self):
        """Generate timing summary"""
        summary_parts = []
        
        for algo, stats in self.algorithm_stats.items():
            if stats['searches'] > 0:
                avg_time = stats['total_time'] / stats['searches']
                summary_parts.append(f"{algo}: {avg_time:.3f}s")
        
        return " | ".join(summary_parts) if summary_parts else "No timing data"

    def get_performance_stats(self):
        """Get algorithm performance statistics"""
        return self.algorithm_stats.copy()

    def reset_stats(self):
        """Reset performance statistics"""
        for algo in self.algorithm_stats:
            self.algorithm_stats[algo] = {'total_time': 0, 'searches': 0}