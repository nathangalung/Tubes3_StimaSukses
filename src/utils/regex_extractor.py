"""regex-based information extraction - improved work experience detection"""

import re
from typing import List, Dict, Optional
from database.models import CVSummary, JobHistory, Education

class RegexExtractor:
    """extract information using improved regex patterns"""
    
    def __init__(self):
        self.section_keywords = {
            'summary': ['SUMMARY', 'PROFILE', 'OVERVIEW', 'OBJECTIVE', 'PROFESSIONAL SUMMARY', 'EXECUTIVE PROFILE', 'ABOUT', 'CAREER SUMMARY'],
            'skills': ['SKILLS', 'TECHNICAL SKILLS', 'PROFESSIONAL SKILLS', 'CORE COMPETENCIES', 'HIGHLIGHTS', 'ACCOMPLISHMENTS', 'SKILL HIGHLIGHTS', 'TECHNICAL COMPETENCIES'],
            'experience': ['EXPERIENCE', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT HISTORY', 'CAREER HISTORY', 'ACTIVITIES', 'MEDIA ACTIVITIES', 'WORK ACTIVITIES', 'EMPLOYMENT', 'CAREER', 'WORK EXPERIENCE'],
            'education': ['EDUCATION', 'EDUCATIONAL BACKGROUND', 'ACADEMIC HISTORY', 'ACADEMIC QUALIFICATIONS', 'EDUCATION BACKGROUND']
        }
        
        # improved date patterns for work experience
        self.date_patterns = [
            # standard formats
            r'\b\d{1,2}\/\d{4}\s*[-–]\s*(?:\d{1,2}\/\d{4}|Present|Current|Now)\b',
            r'\b\d{4}\s*[-–]\s*(?:\d{4}|Present|Current|Now)\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current|Now)\b',
            
            # alternative formats with "to"
            r'\b\d{1,2}\/\d{4}\s+(?:to|To|TO)\s+(?:\d{1,2}\/\d{4}|Present|Current|Now)\b',
            r'\b\d{4}\s+(?:to|To|TO)\s+(?:\d{4}|Present|Current|Now)\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s+(?:to|To|TO)\s+(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current|Now)\b',
            
            # flexible formats
            r'\b\d{4}\s*[\/\-–]\s*\d{4}\b',
            r'\b\d{1,2}\/\d{4}\s*[\/\-–]\s*\d{1,2}\/\d{4}\b',
            
            # single date with present
            r'\b\d{4}\s*[-–]\s*(?:Present|Current|Now)\b',
            r'\b\d{1,2}\/\d{4}\s*[-–]\s*(?:Present|Current|Now)\b'
        ]
        
        # job position indicators
        self.job_indicators = [
            r'\b(?:Manager|Director|Analyst|Developer|Engineer|Specialist|Coordinator|Assistant|Executive|Officer|Lead|Senior|Junior|Intern|Consultant|Administrator)\b',
            r'\b(?:CEO|CTO|CFO|VP|President|Head|Chief)\b',
            r'\b(?:Software|Data|Project|Marketing|Sales|HR|IT|Finance|Operations|Quality|Business|Technical|Product)\b'
        ]
    
    def extract_summary(self, text: str) -> CVSummary:
        """extract complete cv summary with improved work experience detection"""
        if not text or len(text) < 10:
            return self._create_empty_summary()
        
        # normalize text for better parsing
        normalized_text = self._normalize_text(text)
        
        # extract components
        contact_info = self.extract_contact_info(normalized_text)
        skills = self.extract_skills(normalized_text)
        job_history = self.extract_job_history(normalized_text)
        education = self.extract_education(normalized_text)
        summary_text = self._extract_summary_text(normalized_text)
        
        # debug output
        print(f"regex extraction results:")
        print(f"  contact: {len(contact_info)} items")
        print(f"  skills: {len(skills)} items")
        print(f"  jobs: {len(job_history)} items")
        print(f"  education: {len(education)} items")
        
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
    
    def _normalize_text(self, text: str) -> str:
        """normalize text for better regex matching"""
        # fix common line break issues
        text = re.sub(r'(\d{1,2}/\d{4})\s*\n\s*(?:-|–|to|To|TO)\s*\n\s*(Present|Current|Now|\d{1,2}/\d{4})', r'\1 - \2', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d{4})\s*\n\s*(?:-|–|to|To|TO)\s*\n\s*(Present|Current|Now|\d{4})', r'\1 - \2', text, flags=re.IGNORECASE)
        
        # fix month-year patterns
        text = re.sub(r'([A-Za-z]+ \d{4})\s*\n\s*(?:-|–|to|To|TO)\s*\n\s*(Present|Current|Now|[A-Za-z]+ \d{4})', r'\1 - \2', text, flags=re.IGNORECASE)
        
        # normalize multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
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
        
        # extract name from beginning
        lines = text.split()[:15]
        potential_names = []
        
        skip_words = {'director', 'manager', 'senior', 'executive', 'summary', 'profile', 'skilled', 'experienced', 'innovative', 'professional', 'cv', 'resume'}
        
        for i, word in enumerate(lines):
            if word.lower() not in skip_words and len(word) > 2 and word.isalpha():
                if i + 1 < len(lines) and lines[i + 1].lower() not in skip_words and lines[i + 1].isalpha():
                    name_candidate = f"{word} {lines[i + 1]}"
                    if len(name_candidate) < 50:
                        potential_names.append(name_candidate)
                        break
        
        if potential_names:
            contact['name'] = potential_names[0]
        
        return contact
    
    def _extract_section_content(self, text: str, section_keywords: List[str]) -> Optional[str]:
        """extract content from specific section with improved patterns"""
        if not text or not section_keywords:
            return None
        
        for keyword in section_keywords:
            # multiple patterns to catch different text formats
            patterns = [
                # keyword followed by content until next section
                rf'{re.escape(keyword)}\s*:?\s*(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES|EMPLOYMENT|CAREER|WORK)\s*:?|\Z)',
                
                # keyword on separate line
                rf'\n{re.escape(keyword)}\s*:?\s*\n(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES|EMPLOYMENT|CAREER|WORK)\s*:?|\Z)',
                
                # keyword at start
                rf'^{re.escape(keyword)}\s*:?\s*(.*?)(?=\n(?:SKILLS|EXPERIENCE|EDUCATION|SUMMARY|PROFILE|HIGHLIGHTS|ACCOMPLISHMENTS|ACTIVITIES|CERTIFICATIONS|AWARDS|PROJECTS|REFERENCES|EMPLOYMENT|CAREER|WORK)\s*:?|\Z)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if content and len(content) > 10:
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
            
            # skip job activity lines
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
            
            # clean bullet points
            line = re.sub(r'^[\-\*\•\d+\.\)]\s*', '', line).strip()
            if not line:
                continue
            
            # handle categorized skills
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
        """extract work experience with improved detection"""
        print("extracting job history...")
        
        # try structured section first
        content = self._extract_section_content(text, self.section_keywords['experience'])
        
        if not content:
            print("no structured experience section found, trying alternative methods")
            # fallback: search entire text for date patterns
            content = self._find_experience_by_dates(text)
        
        if not content:
            print("no work experience content found")
            return []
        
        print(f"found experience content: {len(content)} characters")
        
        jobs = []
        
        # method 1: find by date patterns
        jobs_from_dates = self._extract_jobs_by_dates(content)
        if jobs_from_dates:
            jobs.extend(jobs_from_dates)
            print(f"found {len(jobs_from_dates)} jobs using date patterns")
        
        # method 2: find by job titles/companies
        if not jobs:
            jobs_from_titles = self._extract_jobs_by_titles(content)
            if jobs_from_titles:
                jobs.extend(jobs_from_titles)
                print(f"found {len(jobs_from_titles)} jobs using title patterns")
        
        # method 3: simple text blocks
        if not jobs:
            jobs_from_blocks = self._extract_jobs_from_blocks(content)
            if jobs_from_blocks:
                jobs.extend(jobs_from_blocks)
                print(f"found {len(jobs_from_blocks)} jobs using text blocks")
        
        print(f"total jobs extracted: {len(jobs)}")
        return jobs[:10]
    
    def _find_experience_by_dates(self, text: str) -> Optional[str]:
        """find experience section by looking for date patterns"""
        # combine all date patterns
        combined_pattern = '|'.join(f'({pattern})' for pattern in self.date_patterns)
        
        # find all date matches with context
        matches = []
        for match in re.finditer(combined_pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end]
            matches.append((match.start(), match.end(), context))
        
        if matches:
            # find largest cluster of dates
            start_pos = min(match[0] for match in matches) - 300
            end_pos = max(match[1] for match in matches) + 300
            
            start_pos = max(0, start_pos)
            end_pos = min(len(text), end_pos)
            
            experience_text = text[start_pos:end_pos]
            print(f"found experience section by dates: {len(experience_text)} characters")
            return experience_text
        
        return None
    
    def _extract_jobs_by_dates(self, content: str) -> List[JobHistory]:
        """extract jobs using date pattern recognition"""
        jobs = []
        
        # find all date patterns
        combined_pattern = '|'.join(f'({pattern})' for pattern in self.date_patterns)
        matches = list(re.finditer(combined_pattern, content, re.IGNORECASE))
        
        print(f"found {len(matches)} date matches")
        
        for i, match in enumerate(matches):
            date_str = match.group().strip()
            print(f"processing date: {date_str}")
            
            # parse date range
            start_date, end_date = self._parse_date_range(date_str)
            
            if not start_date:
                continue
            
            # extract job details around this date
            job_start = max(0, match.start() - 300)
            job_end = match.end() + 300
            
            if i + 1 < len(matches):
                job_end = min(job_end, matches[i + 1].start())
            
            job_text = content[job_start:job_end].strip()
            
            # parse job information
            position, company, description = self._parse_job_details(job_text, date_str)
            
            if position and position.strip():
                job = JobHistory(
                    position=position,
                    company=company or 'Unknown Company',
                    start_date=start_date,
                    end_date=end_date,
                    description=description
                )
                jobs.append(job)
                print(f"extracted job: {position} at {company}")
        
        return jobs
    
    def _extract_jobs_by_titles(self, content: str) -> List[JobHistory]:
        """extract jobs by looking for job title patterns"""
        jobs = []
        
        # patterns that indicate job titles
        title_patterns = [
            r'\b(?:Manager|Director|Analyst|Developer|Engineer|Specialist|Coordinator|Assistant|Executive|Officer|Lead|Senior|Junior)\b[^\n]{0,50}',
            r'\b(?:CEO|CTO|CFO|VP|President|Head|Chief)\b[^\n]{0,50}',
            r'\b(?:Software|Data|Project|Marketing|Sales|HR|IT|Finance|Operations|Quality|Business|Technical|Product)\s+(?:Manager|Director|Analyst|Developer|Engineer|Specialist|Coordinator|Assistant|Executive|Officer|Lead|Senior|Junior)\b'
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                title = match.group().strip()
                
                # get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                
                # look for dates in context
                date_match = None
                for date_pattern in self.date_patterns:
                    date_match = re.search(date_pattern, context, re.IGNORECASE)
                    if date_match:
                        break
                
                if date_match:
                    start_date, end_date = self._parse_date_range(date_match.group())
                    
                    job = JobHistory(
                        position=title,
                        company='Unknown Company',
                        start_date=start_date,
                        end_date=end_date,
                        description=None
                    )
                    jobs.append(job)
                    print(f"extracted job by title: {title}")
        
        return jobs[:5]
    
    def _extract_jobs_from_blocks(self, content: str) -> List[JobHistory]:
        """extract jobs from text blocks"""
        jobs = []
        
        # split content into potential job blocks
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            block = block.strip()
            if len(block) < 20:
                continue
            
            # check if block contains date
            has_date = False
            for pattern in self.date_patterns:
                if re.search(pattern, block, re.IGNORECASE):
                    has_date = True
                    break
            
            if not has_date:
                continue
            
            # extract first line as potential job title
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            if lines:
                position = lines[0]
                
                # clean up position
                position = re.sub(r'^\d+\.\s*', '', position)
                position = re.sub(r'^[-*•]\s*', '', position)
                
                if len(position) > 5 and len(position) < 100:
                    job = JobHistory(
                        position=position,
                        company='Unknown Company',
                        start_date='Unknown',
                        end_date='Unknown',
                        description=None
                    )
                    jobs.append(job)
                    print(f"extracted job from block: {position}")
        
        return jobs
    
    def _parse_date_range(self, date_str: str) -> tuple:
        """parse date range from string"""
        # common separators
        separators = [' to ', ' - ', ' – ', ' TO ', '-', '–', 'to', 'To', 'TO']
        
        for sep in separators:
            if sep in date_str:
                parts = [part.strip() for part in date_str.split(sep, 1)]
                if len(parts) == 2:
                    return parts[0], parts[1]
        
        # single date
        return date_str, 'Present'
    
    def _parse_job_details(self, job_text: str, date_str: str) -> tuple:
        """parse job details from text"""
        lines = [line.strip() for line in job_text.split('\n') if line.strip()]
        
        position = None
        company = None
        description = None
        
        # remove date from lines
        clean_lines = []
        for line in lines:
            if date_str not in line:
                clean_lines.append(line)
        
        if clean_lines:
            # first non-date line is likely position
            position = clean_lines[0]
            position = re.sub(r'^\d+\.\s*', '', position)
            position = re.sub(r'^[-*•]\s*', '', position)
            
            # second line might be company
            if len(clean_lines) > 1:
                second_line = clean_lines[1]
                
                # check if it looks like a company name
                if not any(second_line.lower().startswith(verb) for verb in ['developed', 'managed', 'led', 'created', 'implemented']):
                    company = second_line
                
            # remaining lines as description
            if len(clean_lines) > 2:
                desc_lines = clean_lines[2:] if company else clean_lines[1:]
                if desc_lines:
                    description = ' '.join(desc_lines)
        
        return position, company, description
    
    def extract_education(self, text: str) -> List[Education]:
        """extract education information"""
        content = self._extract_section_content(text, self.section_keywords['education'])
        
        if not content:
            # fallback: search for education keywords
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