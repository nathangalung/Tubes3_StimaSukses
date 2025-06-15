"""regex-based information extraction - working version"""

import re
from typing import List, Dict, Optional
from database.models import CVSummary, JobHistory, Education

class RegexExtractor:
    """extract information using proven regex patterns"""
    
    def __init__(self):
        self.section_keywords = {
            'summary': ['SUMMARY', 'PROFILE', 'OVERVIEW', 'OBJECTIVE', 'PROFESSIONAL SUMMARY', 'EXECUTIVE PROFILE'],
            'skills': ['SKILLS', 'TECHNICAL SKILLS', 'PROFESSIONAL SKILLS', 'CORE COMPETENCIES', 'HIGHLIGHTS', 'ACCOMPLISHMENTS', 'SKILL HIGHLIGHTS'],
            'experience': ['EXPERIENCE', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT HISTORY', 'CAREER HISTORY', 'ACTIVITIES', 'MEDIA ACTIVITIES', 'WORK ACTIVITIES'],
            'education': ['EDUCATION', 'EDUCATIONAL BACKGROUND', 'ACADEMIC HISTORY', 'ACADEMIC QUALIFICATIONS']
        }
        self.date_patterns = [
            r'\b\d{1,2}/\d{4}\s*[-–]\s*(?:\d{1,2}/\d{4}|Present|Current)\b',
            r'\b\d{4}\s*[-–]\s*(?:\d{4}|Present|Current)\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[-–]\s*(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|Present|Current)\b',
            r'\b\d{1,2}/\d{4}\s+to\s+(?:\d{1,2}/\d{4}|Present|Current)\b',
            r'\b\d{4}\s+to\s+(?:\d{4}|Present|Current)\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s+to\s+(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|Present|Current)\b',
            r'\b\d{1,2}/\d{4}.*?(?:Present|Current|\d{1,2}/\d{4})\b',
            r'\b\d{4}.*?(?:Present|Current|\d{4})\b'
        ]
    
    def extract_summary(self, text: str) -> CVSummary:
        """extract complete cv summary"""
        if not text or len(text) < 10:
            return self._create_empty_summary()
        
        # extract components menggunakan method yang sudah terbukti
        contact_info = self.extract_contact_info(text)
        skills = self.extract_skills(text)
        job_history = self.extract_job_history(text)
        education = self.extract_education(text)
        summary_text = self._extract_summary_text(text)
        
        # create cv summary
        cv_summary = CVSummary(
            name=contact_info.get('name', 'unknown'),
            summary=summary_text,
            skills=skills,
            job_history=job_history,
            education=education,
            contact_info=contact_info
        )
        
        return cv_summary
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """extract contact information"""
        contact = {}
        
        # extract email
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        email_matches = email_pattern.findall(text)
        if email_matches:
            contact['email'] = email_matches[0]
        
        # extract phone
        phone_patterns = [
            re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\d{3}[-.\s]?\d{4}'),
        ]
        
        for pattern in phone_patterns:
            phone_matches = pattern.findall(text)
            if phone_matches:
                contact['phone'] = phone_matches[0]
                break
        
        # extract name dari awal text
        lines = text.split()[:15]  # ambil 15 kata pertama
        potential_names = []
        
        skip_words = {'director', 'manager', 'senior', 'executive', 'summary', 'profile', 'skilled', 'experienced', 'innovative', 'professional'}
        
        for i, word in enumerate(lines):
            if word.lower() not in skip_words and len(word) > 2 and word.isalpha():
                # coba ambil 2-3 kata sebagai nama
                if i + 1 < len(lines) and lines[i + 1].lower() not in skip_words and lines[i + 1].isalpha():
                    name_candidate = f"{word} {lines[i + 1]}"
                    if len(name_candidate) < 50:
                        potential_names.append(name_candidate)
                        break
        
        if potential_names:
            contact['name'] = potential_names[0]
        
        return contact
    
    def _fix_text_issues(self, text: str) -> str:
        """fix common text extraction issues"""
        text = re.sub(r'(\d{1,2}/\d{4})\s*\n\s*to\s*\n\s*(Current|Present|\d{1,2}/\d{4})', r'\1 to \2', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d{4})\s*\n\s*to\s*\n\s*(Current|Present|\d{4})', r'\1 to \2', text, flags=re.IGNORECASE)
        text = re.sub(r'(\w+ \d{4})\s*\n\s*to\s*\n\s*(Current|Present|\w+ \d{4})', r'\1 to \2', text, flags=re.IGNORECASE)
        return text
    
    def _extract_section_content(self, text: str, section_keywords: List[str]) -> Optional[str]:
        """extract content dari section tertentu"""
        if not text or not section_keywords:
            return None
        
        text = self._fix_text_issues(text)
        
        for keyword in section_keywords:
            # untuk single line text, gunakan pattern yang lebih fleksibel
            patterns = [
                # pattern untuk single line text
                rf'{re.escape(keyword)}\s+(.*?)(?=\s+(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES)\s+|$)',
                # pattern dengan newline
                rf'\n{re.escape(keyword)}\n\n(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES)\n|\Z)',
                rf'\n{re.escape(keyword)}\n(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES)\n|\Z)',
                rf'^{re.escape(keyword)}\n\n(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES)\n|\Z)',
                rf'^{re.escape(keyword)}\n(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES)\n|\Z)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if content:
                        return content
        
        return None
    
    def _extract_summary_text(self, text: str) -> Optional[str]:
        """extract professional summary"""
        content = self._extract_section_content(text, self.section_keywords['summary'])
        if content:
            summary = re.sub(r'\s*\n\s*', ' ', content)
            summary = re.sub(r'\s+', ' ', summary)
            return summary.strip()
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """extract skills list"""
        content = self._extract_section_content(text, self.section_keywords['skills'])
        if not content:
            return []
        
        skills = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # skip lines yang jelas bukan skills
            skip_patterns = [
                r'^(Developed|Managed|Led|Created|Implemented|Supervised|Coordinated|Analyzed|Designed|Maintained|Operated|Assisted|Prepared|Organized|Handled|Processed|Followed|Consistently|Ensured|Provided|Supported|Built|Established|Improved|Increased|Reduced)',
                r'^\d{2,4}/\d{4}',
                r'^(January|February|March|April|May|June|July|August|September|October|November|December)',
                r'^(Company|Corporation|Inc|Ltd|LLC)',
                r'^\d+\s+(years?|months?)',
                r'^(at|in|for|with)\s+',
                r'years? of experience',
                r'responsible for',
                r'worked with',
            ]
            
            if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue
            
            # bersihkan bullet points
            line = re.sub(r'^[\-\*\•\d+\.\)]\s*', '', line).strip()
            if not line:
                continue
            
            # handle format "Category: skill1, skill2"
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    skills_text = parts[1].strip()
                    
                    if category and len(category) < 50:
                        skills.append(category)
                    
                    if ',' in skills_text:
                        individual_skills = [s.strip() for s in skills_text.split(',')]
                        skills.extend([s for s in individual_skills if s and 2 < len(s) < 50])
                    else:
                        if skills_text and 2 < len(skills_text) < 50:
                            skills.append(skills_text)
            
            # handle comma-separated skills
            elif ',' in line and len(line) > 30:
                line_skills = [skill.strip() for skill in line.split(',')]
                skills.extend([s for s in line_skills if s and 2 < len(s) < 50])
            
            # single skill per line
            else:
                if 2 < len(line) < 80:
                    skills.append(line)
        
        # clean up skills
        cleaned_skills = []
        for skill in skills:
            skill = re.sub(r'^(Knowledge of|Experience with|Proficient in|Skilled in|Expert in|Familiar with)\s+', '', skill, flags=re.IGNORECASE)
            skill = skill.rstrip('.')
            skill = skill.strip()
            
            if skill and skill not in cleaned_skills:
                cleaned_skills.append(skill)
        
        return cleaned_skills[:20]
    
    def extract_job_history(self, text: str) -> List[JobHistory]:
        """extract work experience"""
        content = self._extract_section_content(text, self.section_keywords['experience'])
        if not content:
            return []
        
        jobs = []
        
        # gabungkan semua date patterns
        combined_pattern = '|'.join(f'({pattern})' for pattern in self.date_patterns)
        matches = list(re.finditer(combined_pattern, content, re.IGNORECASE))
        
        if not matches:
            # fallback patterns untuk format yang lebih liberal
            liberal_patterns = [
                r'\d{2}/\d{4}.*?(?:Current|Present)',
                r'\d{4}.*?(?:Current|Present)',
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}.*?(?:Current|Present)'
            ]
            
            for pattern in liberal_patterns:
                liberal_matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
                if liberal_matches:
                    matches = liberal_matches
                    break
        
        for i, match in enumerate(matches):
            # parse date range
            date_str = match.group().strip()
            separators = [' to ', ' - ', ' – ', '-', '–', 'to']
            date_parts = None
            
            for sep in separators:
                if sep in date_str:
                    date_parts = [part.strip() for part in date_str.split(sep, 1)]
                    if len(date_parts) == 2:
                        break
            
            if not date_parts or len(date_parts) != 2:
                continue
            
            start_date = date_parts[0]
            end_date = date_parts[1]
            
            # extract job details setelah date
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
                job_text = content[start_pos:end_pos].strip()
            else:
                job_text = content[start_pos:].strip()
            
            if job_text:
                lines = [line.strip() for line in job_text.split('\n') if line.strip()]
                
                if lines:
                    position = lines[0]
                    company = 'Unknown Company'
                    description = None
                    
                    if len(lines) > 1:
                        second_line = lines[1]
                        # jika line kedua bukan description, anggap sebagai company
                        if not any(second_line.startswith(verb) for verb in ['Developed', 'Managed', 'Led', 'Created', 'Implemented']):
                            company = second_line
                            description_start = 2
                        else:
                            description_start = 1
                    else:
                        description_start = 1
                    
                    if len(lines) > description_start:
                        description = ' '.join(lines[description_start:])
                    
                    jobs.append(JobHistory(
                        position=position,
                        company=company,
                        start_date=start_date,
                        end_date=end_date,
                        description=description
                    ))
        
        return jobs[:10]
    
    def extract_education(self, text: str) -> List[Education]:
        """extract education information"""
        content = self._extract_section_content(text, self.section_keywords['education'])
        
        if not content:
            # fallback: cari education keywords di seluruh text
            edu_keywords = ['Bachelor', 'Master', 'PhD', 'University', 'College', 'Degree', 'MBA', 'BS', 'BA', 'MS', 'MA']
            for keyword in edu_keywords:
                pattern = rf'[^.]*{re.escape(keyword)}[^.]*\.?'
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    content = ' '.join(matches)
                    break
        
        if not content:
            return []
        
        education_list = []
        
        # extract year
        year_matches = re.findall(r'\b(19[8-9]\d|20[0-3]\d)\b', content)
        graduation_year = year_matches[-1] if year_matches else None
        
        # extract degree
        degree_patterns = [
            r'\b(Bachelor\s+of\s+[A-Za-z\s]+)',
            r'\b(Master\s+of\s+[A-Za-z\s]+)',
            r'\b(PhD\s+in\s+[A-Za-z\s]+)',
            r'\b(Associate\s+of\s+[A-Za-z\s]+)',
            r'\b(MBA|MS|BS|BA|MA|M\.Eng|M\.Sc|B\.Sc)\b',
            r'\b(High School Diploma|Secondary School)',
            r'\b(Certificate|Diploma)\s+[A-Za-z\s]*'
        ]
        
        degree = None
        for pattern in degree_patterns:
            degree_match = re.search(pattern, content, re.IGNORECASE)
            if degree_match:
                degree = degree_match.group().strip()
                break
        
        # extract university
        uni_patterns = [
            r'\b([A-Z][A-Za-z\s]*(?:University|College|Institute|School|Academy)[A-Za-z\s]*)',
            r'\b(University\s+of\s+[A-Za-z\s]+)',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:University|College|Institute|School))'
        ]
        
        institution = None
        for pattern in uni_patterns:
            uni_match = re.search(pattern, content, re.IGNORECASE)
            if uni_match:
                institution = uni_match.group().strip()
                institution = re.sub(r'\s*[,–-].*$', '', institution)
                break
        
        if degree or institution or graduation_year:
            education_list.append(Education(
                degree=degree or 'Degree',
                institution=institution or 'Unknown Institution',
                graduation_year=graduation_year
            ))
        
        return education_list[:5]
    
    def _create_empty_summary(self) -> CVSummary:
        """create empty cv summary"""
        return CVSummary(
            name="unknown",
            summary=None,
            skills=[],
            job_history=[],
            education=[],
            contact_info={}
        )

def test_regex_extractor():
    """test regex extraction dengan data real"""
    extractor = RegexExtractor()
    
    # sample text dari debug output sebelumnya
    sample_text = """DIRECTOR OF INFORMATION TECHNOLOGY Executive Profile Innovative executive and technology professional with strong work ethic and excellent communication skills, experienced in high-volume, multi-unit, retail and business operations. Skill Highlights Microsoft Server 2003, 2008, 2012 Exchange Server 2007, 2010 VMware ESXi VMware vCenter VMware Horizon View 5.x, 6.x, and 7.x Microsoft Hyper-V Cisco UCM and Unity Help Desk ITIL Service Catalog Vendor Management Budgeting Project Management SLA Management Asset Management Professional Experience Director of Information Technology 11/2012 to Current Company Name City , State Developed and implemented the IT strategy for the organization including software, support and infrastructure IT Administrator 03/2008 to 11/2012 Company Name City , State Planned, installed and managed Microsoft domain environment Education Bachelor of Science : Management Information Systems Cardinal Stritch University City , State"""
    
    print("=== regex extractor test dengan working version ===")
    summary = extractor.extract_summary(sample_text)
    
    print(f"name: {summary.name}")
    print(f"skills ({len(summary.skills)}): {summary.skills}")
    print(f"jobs ({len(summary.job_history)}):")
    for i, job in enumerate(summary.job_history):
        print(f"  {i+1}. {job.position} at {job.company} ({job.start_date} - {job.end_date})")
    print(f"education ({len(summary.education)}):")
    for i, edu in enumerate(summary.education):
        print(f"  {i+1}. {edu.degree} from {edu.institution} ({edu.graduation_year})")
    print(f"summary: {summary.summary}")
    
    return summary

if __name__ == "__main__":
    test_result = test_regex_extractor()
    print("regex extractor test completed!")