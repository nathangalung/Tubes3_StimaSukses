"""Regex-based information extraction"""

import re
from typing import List, Dict, Optional
from database.models import CVSummary, JobHistory, Education

class RegexExtractor:
    """Extract information using regex patterns"""
    
    def __init__(self):
        # Initialize regex patterns
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup regex patterns"""
        
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone patterns
        self.phone_patterns = [
            re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\d{3}[-.\s]?\d{4}'),
        ]
        
        # Skills pattern
        self.skills_pattern = re.compile(
            r'\b(?:Python|Java|JavaScript|React|Node\.js|SQL|MongoDB|'
            r'Docker|Kubernetes|AWS|Git|Linux|HTML|CSS|C\+\+|C#|'
            r'Machine Learning|Data Science|Excel|AutoCAD|MATLAB|'
            r'Photoshop|Illustrator|Marketing|Sales|Finance|Accounting)\b',
            re.IGNORECASE
        )
        
        # Job title patterns
        self.job_title_pattern = re.compile(
            r'\b(?:Software Engineer|Developer|Data Scientist|Manager|'
            r'Analyst|Designer|Consultant|Director|Coordinator|'
            r'Specialist|Administrator|Technician|Intern)\b',
            re.IGNORECASE
        )
        
        # Company patterns (common indicators)
        self.company_indicators = re.compile(
            r'\b(?:Inc|Corp|Corporation|Company|Ltd|Limited|LLC|'
            r'Technologies|Solutions|Systems|Group|Pvt)\b',
            re.IGNORECASE
        )
        
        # Education patterns
        self.education_patterns = {
            'degree': re.compile(
                r'\b(?:Bachelor|Master|PhD|Doctorate|Associate|'
                r'B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|MBA)\b',
                re.IGNORECASE
            ),
            'institution': re.compile(
                r'\b(?:University|College|Institute|School)\b',
                re.IGNORECASE
            )
        }
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'\b\d{4}\s*-\s*\d{4}\b'),  # 2020-2023
            re.compile(r'\b\d{4}\s*to\s*\d{4}\b', re.IGNORECASE),  # 2020 to 2023
            re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b', re.IGNORECASE)
        ]
    
    def extract_summary(self, text: str) -> CVSummary:
        """Extract complete CV summary"""
        if not text or len(text) < 10:
            return self._create_empty_summary()
        
        # Extract components
        contact_info = self.extract_contact_info(text)
        skills = self.extract_skills(text)
        job_history = self.extract_job_history(text)
        education = self.extract_education(text)
        summary_text = self.extract_professional_summary(text)
        
        # Create CV summary
        cv_summary = CVSummary(
            name=contact_info.get('name', 'Unknown'),
            summary=summary_text,
            skills=skills,
            job_history=job_history,
            education=education,
            contact_info=contact_info
        )
        
        return cv_summary
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information"""
        contact = {}
        
        # Extract email
        email_matches = self.email_pattern.findall(text)
        if email_matches:
            contact['email'] = email_matches[0]
        
        # Extract phone
        for pattern in self.phone_patterns:
            phone_matches = pattern.findall(text)
            if phone_matches:
                contact['phone'] = phone_matches[0]
                break
        
        # Extract name (first line or words before email)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 0 and len(line) < 50:
                # Simple name detection
                words = line.split()
                if 2 <= len(words) <= 4:  # Typical name length
                    if all(word.isalpha() or word.replace('-', '').isalpha() for word in words):
                        contact['name'] = line
                        break
        
        return contact
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills"""
        skills = set()
        
        # Find skill matches
        skill_matches = self.skills_pattern.findall(text)
        skills.update(skill_matches)
        
        # Look for skills section
        skill_section_pattern = re.compile(
            r'(?:skills?|technologies?|competencies)[\s:]*([^\n]*(?:\n[^\n]*)*?)(?:\n\s*\n|\n[A-Z])',
            re.IGNORECASE | re.MULTILINE
        )
        
        skill_sections = skill_section_pattern.findall(text)
        for section in skill_sections:
            # Extract words that might be skills
            words = re.findall(r'\b[A-Za-z\+\#\.]+\b', section)
            for word in words:
                if len(word) > 2 and word not in {'and', 'the', 'with', 'for', 'etc'}:
                    skills.add(word)
        
        return list(skills)[:15]  # Limit to 15 skills
    
    def extract_job_history(self, text: str) -> List[JobHistory]:
        """Extract work experience"""
        jobs = []
        
        # Look for experience section
        exp_section_pattern = re.compile(
            r'(?:experience|employment|work history)[\s:]*([^\n]*(?:\n[^\n]*)*?)(?:\n\s*\n|\n(?:education|skills))',
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        exp_matches = exp_section_pattern.findall(text)
        
        if exp_matches:
            exp_text = exp_matches[0]
            
            # Find job entries
            job_entries = re.split(r'\n\s*\n', exp_text)
            
            for entry in job_entries:
                if len(entry.strip()) > 20:  # Minimum entry length
                    job = self._parse_job_entry(entry)
                    if job:
                        jobs.append(job)
        
        return jobs[:5]  # Limit to 5 jobs
    
    def _parse_job_entry(self, entry: str) -> Optional[JobHistory]:
        """Parse individual job entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line usually contains position and/or company
        first_line = lines[0]
        
        # Try to extract position
        job_title_matches = self.job_title_pattern.findall(first_line)
        position = job_title_matches[0] if job_title_matches else first_line
        
        # Try to extract company
        company = "Unknown Company"
        for line in lines[:3]:  # Check first 3 lines
            if self.company_indicators.search(line):
                company = line
                break
        
        # Try to extract dates
        date_range = None
        for pattern in self.date_patterns:
            for line in lines:
                date_matches = pattern.findall(line)
                if date_matches:
                    date_range = date_matches[0]
                    break
            if date_range:
                break
        
        # Extract description
        description = ' '.join(lines[1:3]) if len(lines) > 1 else None
        
        return JobHistory(
            position=position,
            company=company,
            start_date=date_range.split('-')[0].strip() if date_range and '-' in date_range else None,
            end_date=date_range.split('-')[1].strip() if date_range and '-' in date_range else None,
            description=description
        )
    
    def extract_education(self, text: str) -> List[Education]:
        """Extract education information"""
        education = []
        
        # Look for education section
        edu_section_pattern = re.compile(
            r'(?:education|academic|qualifications)[\s:]*([^\n]*(?:\n[^\n]*)*?)(?:\n\s*\n|\n(?:experience|skills))',
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        edu_matches = edu_section_pattern.findall(text)
        
        if edu_matches:
            edu_text = edu_matches[0]
            
            # Find degree mentions
            degree_matches = self.education_patterns['degree'].findall(edu_text)
            institution_matches = self.education_patterns['institution'].findall(edu_text)
            
            # Try to pair degrees with institutions
            for i, degree in enumerate(degree_matches):
                institution = institution_matches[i] if i < len(institution_matches) else "Unknown Institution"
                
                # Look for graduation year
                year_pattern = re.compile(r'\b(19|20)\d{2}\b')
                years = year_pattern.findall(edu_text)
                graduation_year = years[0] if years else None
                
                education.append(Education(
                    degree=degree,
                    institution=institution,
                    graduation_year=graduation_year
                ))
        
        return education[:3]  # Limit to 3 education entries
    
    def extract_professional_summary(self, text: str) -> Optional[str]:
        """Extract professional summary"""
        
        # Look for summary section
        summary_patterns = [
            re.compile(
                r'(?:summary|profile|objective|about)[\s:]*([^\n]*(?:\n[^\n]*)*?)(?:\n\s*\n|\n[A-Z])',
                re.IGNORECASE | re.MULTILINE
            ),
            re.compile(
                r'^([^\n]*(?:\n[^\n]*){1,3})(?:\n\s*\n)',
                re.MULTILINE
            )
        ]
        
        for pattern in summary_patterns:
            matches = pattern.findall(text)
            if matches:
                summary = matches[0].strip()
                if len(summary) > 50 and len(summary) < 500:
                    return summary
        
        return None
    
    def _create_empty_summary(self) -> CVSummary:
        """Create empty CV summary"""
        return CVSummary(
            name="Unknown",
            summary=None,
            skills=[],
            job_history=[],
            education=[],
            contact_info={}
        )

def test_regex_extractor():
    """Test regex extraction"""
    extractor = RegexExtractor()
    
    # Sample CV text
    sample_text = """
    John Doe
    Email: john.doe@email.com
    Phone: +1-234-567-8900
    
    SUMMARY
    Experienced software engineer with 5 years in Python development
    
    SKILLS
    Python, Java, SQL, React, Docker, AWS
    
    EXPERIENCE
    Software Engineer
    Tech Corp Inc
    2020-2023
    Developed web applications using Python and React
    
    EDUCATION
    Bachelor of Science
    MIT University
    2018
    """
    
    print("=== REGEX EXTRACTOR TEST ===")
    summary = extractor.extract_summary(sample_text)
    
    print(f"Name: {summary.name}")
    print(f"Email: {summary.contact_info.get('email', 'Not found')}")
    print(f"Phone: {summary.contact_info.get('phone', 'Not found')}")
    print(f"Skills: {summary.skills}")
    print(f"Jobs: {len(summary.job_history)}")
    print(f"Education: {len(summary.education)}")
    
    if summary.job_history:
        job = summary.job_history[0]
        print(f"First job: {job.position} at {job.company}")
    
    return True

if __name__ == "__main__":
    test_regex_extractor()
    print("🎉 Regex extractor test completed!")