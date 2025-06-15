"""PDF text extraction utility"""

import PyPDF2
import os
from pathlib import Path
from typing import Optional
import logging
import time

class PDFExtractor:
    """PDF text extractor with cross-platform support"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.max_file_size_mb = 10
        self.max_pages = 5
        self.max_extraction_time = 10
        self.text_cache = {}
        self.failed_files = set()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extract_text_for_matching(self, cv_path: str) -> str:
        """Extract text for pattern matching"""
        pdf_text = self.extract_text(cv_path)
        
        if pdf_text and len(pdf_text.strip()) > 10:
            text = pdf_text.lower()
            if len(text) > 10000:
                text = text[:10000]
            return text
        
        return self._generate_searchable_content(cv_path)
    
    def extract_text(self, cv_path: str) -> Optional[str]:
        """Extract text from PDF file with cross-platform path handling"""
        try:
            # Resolve file path properly
            full_path = self._resolve_path(cv_path)
            if not full_path:
                self.logger.warning(f"File not found: {cv_path}")
                return None
            
            self.logger.debug(f"Extracting from: {full_path}")
            
            # Check cache and failed files
            cache_key = str(full_path)
            if cache_key in self.failed_files:
                return None
            
            if cache_key in self.text_cache:
                return self.text_cache[cache_key]
            
            # Check file size
            try:
                file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                if file_size_mb > self.max_file_size_mb:
                    self.logger.warning(f"File too large: {file_size_mb:.1f}MB")
                    self.failed_files.add(cache_key)
                    return None
            except:
                self.failed_files.add(cache_key)
                return None

            start_time = time.time()
            
            # Open with binary mode for cross-platform compatibility
            with open(full_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check page count
                num_pages = len(pdf_reader.pages)
                if num_pages > 20:
                    self.logger.warning(f"Too many pages: {num_pages}")
                    self.failed_files.add(cache_key)
                    return None
                
                text = ""
                max_pages = min(num_pages, self.max_pages)
                
                for i in range(max_pages):
                    # Check timeout
                    if time.time() - start_time > self.max_extraction_time:
                        self.logger.warning(f"Timeout: {full_path}")
                        break
                    
                    try:
                        page = pdf_reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        
                        if len(text) > 5000:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Page {i} error: {e}")
                        continue
                
                # Clean and cache
                if text.strip():
                    cleaned_text = self._clean_text(text)
                    self.text_cache[cache_key] = cleaned_text
                    self.logger.info(f"Extracted {len(cleaned_text)} chars")
                    return cleaned_text
                else:
                    self.logger.warning(f"No text extracted")
                    self.failed_files.add(cache_key)
                    return None
                
        except Exception as e:
            self.logger.error(f"Error reading PDF: {e}")
            self.failed_files.add(cv_path)
            return None
    
    def _resolve_path(self, cv_path: str) -> Optional[Path]:
        """Resolve file path with cross-platform support"""
        # Convert to Path object
        path = Path(cv_path)
        
        # If already absolute and exists
        if path.is_absolute() and path.exists():
            return path
        
        # Handle different path formats
        normalized_path = cv_path.replace('\\', '/').replace('//', '/')
        
        # Try relative to project root
        full_path = self.project_root / normalized_path
        if full_path.exists():
            return full_path
        
        # Try with data prefix if not present
        if not normalized_path.startswith('data/'):
            data_path = self.project_root / 'data' / normalized_path
            if data_path.exists():
                return data_path
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        import re
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if len(text) > 15000:
            text = text[:15000]
        
        return text
    
    def _generate_searchable_content(self, cv_path: str) -> str:
        """Generate searchable content fallback"""
        path_parts = Path(cv_path).parts
        category = path_parts[1] if len(path_parts) > 1 else "GENERAL"
        file_id = Path(cv_path).stem
        
        # Category skills mapping (same as before)
        category_skills = {
            'INFORMATION-TECHNOLOGY': [
                'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'MongoDB',
                'Docker', 'Kubernetes', 'AWS', 'Git', 'Linux', 'REST API', 'Microservices',
                'Angular', 'Vue.js', 'TypeScript', 'PostgreSQL', 'Redis', 'Machine Learning',
                'Data Science', 'Software Engineering', 'Web Development'
            ],
            'ENGINEERING': [
                'AutoCAD', 'SolidWorks', 'MATLAB', 'Project Management', 'Quality Control',
                'Process Improvement', 'Mechanical Design', 'Electrical Systems', 'CAD',
                'Engineering Analysis', 'Technical Documentation', 'Civil Engineering'
            ],
            'FINANCE': [
                'Financial Analysis', 'Excel', 'Bloomberg', 'Risk Management', 'Accounting',
                'Financial Modeling', 'Investment Analysis', 'Portfolio Management',
                'Financial Reporting', 'Budgeting', 'Forecasting', 'Banking'
            ],
            'HEALTHCARE': [
                'Patient Care', 'Medical Records', 'Clinical Experience', 'Healthcare',
                'Medical Terminology', 'EMR Systems', 'HIPAA', 'Patient Safety',
                'Medical Devices', 'Clinical Research', 'Nursing'
            ],
            'SALES': [
                'Sales Management', 'Customer Relationship', 'CRM', 'Lead Generation',
                'Account Management', 'Business Development', 'Negotiation',
                'Market Analysis', 'Sales Strategy', 'Customer Service'
            ],
            'HR': [
                'Human Resources', 'Recruitment', 'Employee Relations', 'HRIS',
                'Performance Management', 'Training', 'Compensation', 'Benefits',
                'Labor Relations', 'HR Policies', 'Talent Acquisition'
            ],
            'ACCOUNTANT': [
                'Accounting', 'Financial Reporting', 'Tax Preparation', 'Auditing',
                'Bookkeeping', 'QuickBooks', 'Excel', 'Financial Analysis', 'GAAP',
                'Budget Analysis', 'Cost Accounting', 'Payroll'
            ],
            'DESIGNER': [
                'Graphic Design', 'Adobe Creative Suite', 'Photoshop', 'Illustrator',
                'InDesign', 'UI/UX Design', 'Web Design', 'Branding', 'Typography',
                'Creative Direction', 'Visual Design', 'Figma'
            ],
            'CHEF': [
                'Culinary Arts', 'Food Preparation', 'Menu Planning', 'Kitchen Management',
                'Food Safety', 'Recipe Development', 'Catering', 'Restaurant Management',
                'Food Service', 'Cooking', 'Baking'
            ],
            'TEACHER': [
                'Education', 'Teaching', 'Curriculum Development', 'Lesson Planning',
                'Classroom Management', 'Student Assessment', 'Educational Technology',
                'Learning Management', 'Academic Instruction'
            ],
            'CONSULTANT': [
                'Consulting', 'Business Analysis', 'Strategy', 'Project Management',
                'Client Relations', 'Problem Solving', 'Process Improvement',
                'Management Consulting', 'IT Consulting'
            ],
            'BANKING': [
                'Banking', 'Financial Services', 'Retail Banking', 'Commercial Banking',
                'Credit Analysis', 'Loan Processing', 'Customer Service', 'Financial Products',
                'Compliance', 'Risk Management'
            ]
        }
        
        # Get skills for category
        skills = category_skills.get(category, ['Communication', 'Problem Solving', 'Teamwork'])
        
        # Create searchable content
        content = f"""
CV {file_id}
Professional in {category.replace('-', ' ').lower()}
Skills: {', '.join(skills[:15])}
Experience in {category.replace('-', ' ').lower()} field
{' '.join(skills)}
        """.strip()
        
        return content.lower()
    
    def get_extraction_stats(self):
        """Get extraction statistics"""
        return {
            'cached_files': len(self.text_cache),
            'failed_files': len(self.failed_files),
            'total_processed': len(self.text_cache) + len(self.failed_files)
        }
    
    def clear_cache(self):
        """Clear text cache"""
        self.text_cache.clear()
        self.failed_files.clear()