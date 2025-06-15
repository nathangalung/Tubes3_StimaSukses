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

    def search_cvs(self, keywords, algorithm='KMP', max_results=50, fuzzy_threshold=0.8):
        """Enhanced search with proper algorithm selection"""
        if not keywords:
            return []
        
        # Parse keywords - handle both string and list inputs
        if isinstance(keywords, str):
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        elif isinstance(keywords, list):
            keyword_list = keywords
        else:
            return []
        
        if not keyword_list:
            return []
        
        print(f"🔍 Searching with {algorithm} algorithm")
        print(f"📝 Keywords: {keyword_list}")
        
        # Get resumes
        resumes = self.repo.get_all_resumes()[:self.max_cvs_to_process]
        
        # Initialize timer - FIX: use correct method name
        self.timer.start_total_search()
        
        try:
            # Route to appropriate search method based on algorithm
            if algorithm.upper() == 'KMP':
                results = self._execute_exact_search(resumes, keyword_list, 'KMP', fuzzy_threshold, max_results)
            elif algorithm.upper() == 'BM':
                results = self._execute_exact_search(resumes, keyword_list, 'BM', fuzzy_threshold, max_results)
            elif algorithm.upper() == 'AC':
                results = self._execute_exact_search(resumes, keyword_list, 'AC', fuzzy_threshold, max_results)
            elif algorithm.upper() == 'LEVENSHTEIN':
                results = self._execute_fuzzy_search(resumes, keyword_list, fuzzy_threshold)
            else:
                print(f"⚠️ Unknown algorithm: {algorithm}, using KMP")
                results = self._execute_exact_search(resumes, keyword_list, 'KMP', fuzzy_threshold, max_results)
            
            # Calculate relevance scores
            results = self._calculate_relevance_scores(results, keyword_list)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            limited_results = results[:max_results]
            
            # FIX: use correct method name
            self.timer.stop_total_search()
            
            # Generate timing summary
            timing_info = self._generate_timing_summary()
            
            print(f"✅ Search completed: {len(limited_results)} results")
            return limited_results, timing_info
            
        except Exception as e:
            # FIX: use correct method name
            self.timer.stop_total_search()
            print(f"❌ Search error: {e}")
            raise e

    def _execute_exact_search(self, resumes, keywords, algorithm, fuzzy_threshold, top_n):
        """Execute exact search with fallback"""
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
        
        print(f"✅ Exact: {len(exact_results)} matches in {exact_time:.3f}s")
        
        # Fuzzy fallback if needed
        unfound_keywords = self._get_unfound_keywords(exact_results, keywords)
        fuzzy_results = []
        
        if unfound_keywords and len(exact_results) < top_n:
            print(f"🔍 Fuzzy fallback: {unfound_keywords}")
            
            start_time = time.time()
            fuzzy_resumes = resumes[:50]
            fuzzy_results = self._SearchController__fuzzy_search(fuzzy_resumes, unfound_keywords, fuzzy_threshold)
            fuzzy_time = time.time() - start_time
            
            self.algorithm_stats['LEVENSHTEIN']['total_time'] += fuzzy_time
            self.algorithm_stats['LEVENSHTEIN']['searches'] += 1
            
            print(f"✅ Fuzzy: {len(fuzzy_results)} matches in {fuzzy_time:.3f}s")
        
        return self._combine_results(exact_results, fuzzy_results)

    def _batched_exact_search(self, resumes, keywords, algorithm):
        """Process resumes in batches"""
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for batch_start in range(0, len(resumes), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(resumes))
            batch_resumes = resumes[batch_start:batch_end]
            
            # Update progress
            if self.progress_callback:
                progress = int((batch_start / len(resumes)) * 100)
                self.progress_callback(f"{algorithm}: batch {batch_start//self.batch_size + 1} ({progress}%)")
            
            # Process batch
            batch_results, batch_success, batch_failed = self._process_resume_batch(batch_resumes, keywords, algorithm)
            results.extend(batch_results)
            successful_extractions += batch_success
            failed_extractions += batch_failed
            
        print(f"📊 Batch: {successful_extractions} success, {failed_extractions} failed")
        return results

    def _process_resume_batch(self, batch_resumes, keywords, algorithm):
        """Process single batch"""
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for resume in batch_resumes:
            try:
                # Extract text
                cv_text = self.pdf_extractor.extract_text_for_matching(resume.file_path)
                
                if not cv_text or len(cv_text) < 10:
                    failed_extractions += 1
                    continue
                
                successful_extractions += 1
                
                # Debug first extractions
                if successful_extractions <= 2:
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
        
        return results, successful_extractions, failed_extractions

    def _kmp_search_keywords(self, text, keywords):
        """Search using KMP"""
        matches = {}
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            positions = self.kmp_matcher.search(text_lower, keyword_lower)
            matches[keyword] = len(positions)
        
        return matches

    def _bm_search_keywords(self, text, keywords):
        """Search using Boyer-Moore"""
        matches = {}
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            positions = self.bm_matcher.search(text_lower, keyword_lower)
            matches[keyword] = len(positions)
        
        return matches

    def __fuzzy_search(self, resumes, keywords, threshold):
        """ fuzzy search"""
        results = []
        
        for idx, resume in enumerate(resumes):
            if self.progress_callback and idx % 5 == 0:
                progress = int((idx / len(resumes)) * 100)
                self.progress_callback(f"Fuzzy: {idx+1}/{len(resumes)} ({progress}%)")
            
            try:
                cv_text = self.pdf_extractor.extract_text_for_matching(resume.file_path)
                if not cv_text or len(cv_text) < 10:
                    continue
                
                # Fuzzy matching
                fuzzy_matches = {}
                total_fuzzy_matches = 0
                matched_keywords = []
                
                for keyword in keywords:
                    matches = self.levenshtein_matcher.fuzzy_search_multiple(cv_text, [keyword], threshold)
                    
                    if matches and keyword.lower() in matches:
                        fuzzy_key = f"{keyword} (fuzzy)"
                        match_count = len(matches[keyword.lower()])
                        fuzzy_matches[fuzzy_key] = match_count
                        total_fuzzy_matches += match_count
                        matched_keywords.append(fuzzy_key)
                        print(f"🔍 Fuzzy '{keyword}' {match_count}x in {resume.id}")
                
                if total_fuzzy_matches > 0:
                    result = SearchResult(
                        resume=resume,
                        keyword_matches=fuzzy_matches,
                        total_matches=total_fuzzy_matches,
                        matched_keywords=matched_keywords,
                        fuzzy_matches=fuzzy_matches
                    )
                    result.algorithm_used = 'LEVENSHTEIN'
                    results.append(result)
                    
            except Exception as e:
                print(f"⚠️ Fuzzy error {resume.id}: {e}")
                continue
        
        return results

    def _aho_corasick_search(self, resumes, keywords):
        """Enhanced Aho-Corasick search implementation"""
        results = []
        
        # Build automaton once for all keywords (AC advantage)
        self.aho_corasick.build_automaton(keywords)
        
        for idx, resume in enumerate(resumes):
            if self.progress_callback and idx % 5 == 0:
                progress = int((idx / len(resumes)) * 100)
                self.progress_callback(f"AC: {idx+1}/{len(resumes)} ({progress}%)")
            
            try:
                cv_text = self.pdf_extractor.extract_text_for_matching(resume.file_path)
                if not cv_text or len(cv_text) < 10:
                    continue
                
                # Single traversal multi-pattern search (AC advantage)
                matches = self.aho_corasick.search_multiple(cv_text, keywords)
                
                if matches:
                    keyword_matches = {}
                    total_matches = 0
                    matched_keywords = []
                    
                    for keyword in keywords:
                        keyword_lower = keyword.lower().strip()
                        if keyword_lower in matches:
                            match_count = len(matches[keyword_lower])
                            keyword_matches[keyword] = match_count
                            total_matches += match_count
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
                print(f"⚠️ AC error {resume.id}: {e}")
                continue
        
        return results

    def _calculate_relevance_scores(self, results: List[SearchResult], keywords: List[str]) -> List[SearchResult]:
        """Calculate relevance scores"""
        for result in results:
            base_score = result.total_matches * 10
            
            # Exact match bonus
            exact_bonus = sum(count for key, count in result.keyword_matches.items() 
                            if '(fuzzy)' not in key) * 5
            
            # Keyword coverage bonus
            coverage_ratio = len(result.matched_keywords) / len(keywords)
            coverage_bonus = coverage_ratio * 50
            
            result.relevance_score = base_score + exact_bonus + coverage_bonus
        
        return results

    def _generate_timing_summary(self) -> str:
        """Generate timing summary"""
        base_summary = f"⏱️ Search Performance Summary:\n  • Total Time: {self.timer.total_time:.3f}s"
        
        # Add algorithm performance
        perf_lines = [base_summary, "\n📊 Algorithm Performance:"]
        
        for algo, stats in self.algorithm_stats.items():
            if stats['searches'] > 0:
                avg_time = stats['total_time'] / stats['searches']
                perf_lines.append(f"  • {algo}: avg {avg_time:.3f}s ({stats['searches']} searches)")
        
        return "\n".join(perf_lines)

    def _get_unfound_keywords(self, exact_results, keywords):
        """Get unfound keywords"""
        found_keywords = set()
        for result in exact_results:
            for keyword in result.matched_keywords:
                clean_keyword = keyword.replace(' (fuzzy)', '')
                found_keywords.add(clean_keyword)
        
        return [kw for kw in keywords if kw not in found_keywords]

    def _combine_results(self, exact_results, fuzzy_results):
        """Combine exact and fuzzy results"""
        exact_resume_ids = {result.resume.id for result in exact_results}
        combined = exact_results[:]
        
        for fuzzy_result in fuzzy_results:
            if fuzzy_result.resume.id not in exact_resume_ids:
                combined.append(fuzzy_result)
        
        return combined

    def _execute_fuzzy_search(self, resumes, keywords, threshold):
        """Execute fuzzy-only search"""
        
        print(f"🔍 Fuzzy-only: threshold {threshold}")
        
        start_time = time.time()
        results = self._SearchController__fuzzy_search(resumes, keywords, threshold)
        fuzzy_time = time.time() - start_time
        
        self.algorithm_stats['LEVENSHTEIN']['total_time'] += fuzzy_time
        self.algorithm_stats['LEVENSHTEIN']['searches'] += 1
        
        print(f"✅ Fuzzy completed: {len(results)} results in {fuzzy_time:.3f}s")
        
        return results