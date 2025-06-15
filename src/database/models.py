"""Database models for ATS"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import date

@dataclass
class Resume:
    """Resume model"""
    id: str
    category: str
    file_path: str
    name: str
    phone: Optional[str] = None
    birthdate: Optional[date] = None
    address: Optional[str] = None

@dataclass
class SearchResult:
    """Search result model"""
    resume: Resume
    keyword_matches: Dict[str, int]
    total_matches: int
    matched_keywords: List[str]
    algorithm_used: str = ""
    relevance_score: float = 0.0
    fuzzy_matches: Dict[str, int] = None

@dataclass
class SearchTimingInfo:
    """Search timing information"""
    total_time: float
    exact_search_time: float
    fuzzy_search_time: float
    algorithm_used: str
    cvs_processed: int

@dataclass
class JobHistory:
    """Job history model"""
    position: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Education:
    """Education model with GPA support"""
    degree: str
    institution: str
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

@dataclass
class CVSummary:
    """CV summary model"""
    name: str
    summary: Optional[str] = None
    skills: List[str] = None
    job_history: List[JobHistory] = None
    education: List[Education] = None
    contact_info: Dict[str, str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.job_history is None:
            self.job_history = []
        if self.education is None:
            self.education = []
        if self.contact_info is None:
            self.contact_info = {}