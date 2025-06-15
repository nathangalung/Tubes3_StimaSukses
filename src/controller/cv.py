"""cv operations controller"""

import os
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from database.models import CVSummary
from database.repo import ResumeRepository
from utils.pdf_extractor import PDFExtractor
from utils.regex_extractor import RegexExtractor

class CVController:
    """cv operations controller"""
    
    def __init__(self):
        self.repo = ResumeRepository()
        self.pdf_extractor = PDFExtractor()
        self.regex_extractor = RegexExtractor()
    
    def get_cv_text(self, resume_id: str) -> Optional[str]:
        """get cv text for matching"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return None
        
        return self.pdf_extractor.extract_text_for_matching(resume.file_path)
    
    def get_cv_summary(self, resume_id: str) -> Optional[CVSummary]:
        """generate cv summary using regex"""
        print(f"generating summary for {resume_id}")
        
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"resume {resume_id} not found")
            return None
        
        # check file path format
        file_path = resume.file_path
        
        # handle different path formats
        if not os.path.exists(file_path):
            # try relative to project root
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / file_path
            if full_path.exists():
                file_path = str(full_path)
            else:
                print(f"file not found: {file_path}")
                return None
        
        # extract text
        cv_text = self.pdf_extractor.extract_text(file_path)
        if not cv_text:
            print(f"failed to extract text from {file_path}")
            return None
        
        print(f"extracted {len(cv_text)} characters")
        
        # extract summary using regex
        summary = self.regex_extractor.extract_summary(cv_text)
        
        # enhance with database info
        if resume.name and resume.name != "unknown":
            summary.name = resume.name
        if resume.phone:
            summary.contact_info['phone'] = resume.phone
        if resume.address:
            summary.contact_info['address'] = resume.address
        
        print(f"generated summary: {len(summary.skills)} skills, {len(summary.job_history)} jobs, {len(summary.education)} education")
        
        return summary
    
    def open_cv_file(self, resume_id: str) -> bool:
        """open cv file berdasarkan struktur project"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"resume not found: {resume_id}")
            return False
        
        # resolve file path berdasarkan struktur project
        file_path = resume.file_path
        
        # jika path tidak absolute, resolve dari project root
        if not os.path.isabs(file_path):
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / file_path
            if full_path.exists():
                file_path = str(full_path.resolve())
            else:
                print(f"cv file not found: {file_path}")
                print(f"tried path: {full_path}")
                return False
        else:
            if not os.path.exists(file_path):
                print(f"cv file not found: {file_path}")
                return False
            file_path = os.path.abspath(file_path)
        
        try:
            print(f"opening cv: {file_path}")
            
            # open berdasarkan platform
            if platform.system() == 'Windows':
                os.startfile(file_path)
                print("opened with windows default app")
                return True
                
            elif platform.system() == 'Darwin':  # macos
                subprocess.run(['open', file_path], check=True)
                print("opened with macos default app")
                return True
                
            else:  # linux
                # prioritas: xdg-open -> browser -> pdf viewer
                
                # 1. xdg-open (recommended)
                if shutil.which('xdg-open'):
                    try:
                        subprocess.run(['xdg-open', file_path], 
                                     check=True, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     timeout=5)
                        print("opened with xdg-open")
                        return True
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        pass
                
                # 2. browser dengan file protocol
                browsers = ['firefox', 'google-chrome', 'chromium-browser', 'chromium']
                file_url = f"file://{file_path}"
                
                for browser in browsers:
                    if shutil.which(browser):
                        try:
                            subprocess.run([browser, file_url], 
                                         check=False,
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         timeout=5)
                            print(f"opened with {browser}")
                            return True
                        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                            continue
                
                # 3. pdf viewers
                pdf_viewers = ['evince', 'okular', 'atril', 'zathura', 'mupdf']
                
                for viewer in pdf_viewers:
                    if shutil.which(viewer):
                        try:
                            subprocess.run([viewer, file_path], 
                                         check=False,
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         timeout=5)
                            print(f"opened with {viewer}")
                            return True
                        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                            continue
                
                print("no pdf viewer found")
                print(f"file path: {file_path}")
                print("install: xdg-open, firefox, atau evince")
                return False
            
        except Exception as e:
            print(f"error opening cv: {e}")
            return False
    
    def get_resume_info(self, resume_id: str):
        """get basic resume info"""
        return self.repo.get_resume_by_id(resume_id)
    
    def validate_cv_file(self, resume_id: str) -> bool:
        """validate cv file exists"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        file_path = resume.file_path
        
        # check direct path
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return True
        
        # check relative to project root
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path
        return full_path.exists() and full_path.is_file()
    
    def get_cv_preview(self, resume_id: str, max_length: int = 500) -> Optional[str]:
        """get cv text preview"""
        cv_text = self.get_cv_text(resume_id)
        if not cv_text:
            return None
        
        if len(cv_text) <= max_length:
            return cv_text
        
        return cv_text[:max_length] + "..."