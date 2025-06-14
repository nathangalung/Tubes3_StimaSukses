"""CV operations controller"""

import os
import platform
import subprocess
import shutil
from typing import Optional
from database.models import CVSummary
from database.repo import ResumeRepository
from utils.pdf_extractor import PDFExtractor
from utils.regex_extractor import RegexExtractor

class CVController:
    """CV operations controller"""
    
    def __init__(self):
        self.repo = ResumeRepository()
        self.pdf_extractor = PDFExtractor()
        self.regex_extractor = RegexExtractor()
    
    def get_cv_text(self, resume_id: str) -> Optional[str]:
        """Get CV text for matching"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return None
        
        return self.pdf_extractor.extract_text_for_matching(resume.file_path)
    
    def get_cv_summary(self, resume_id: str) -> Optional[CVSummary]:
        """Generate CV summary using regex"""
        print(f"📄 Generating summary for {resume_id}")
        
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"❌ Resume {resume_id} not found")
            return None
        
        # Extract text
        cv_text = self.pdf_extractor.extract_text(resume.file_path)
        if not cv_text:
            print(f"❌ Failed to extract text from {resume.file_path}")
            return None
        
        print(f"✓ Extracted {len(cv_text)} characters")
        
        # Extract summary using regex
        summary = self.regex_extractor.extract_summary(cv_text)
        
        # Enhance with database info
        if resume.name:
            summary.name = resume.name
        if resume.phone:
            summary.contact_info['phone'] = resume.phone
        if resume.address:
            summary.contact_info['address'] = resume.address
        
        print(f"✓ Generated summary: {len(summary.skills)} skills, {len(summary.job_history)} jobs")
        
        return summary
    
    def open_cv_file(self, resume_id: str) -> bool:
        """Open CV file with default app"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume or not os.path.exists(resume.file_path):
            print(f"❌ CV file not found: {resume_id}")
            return False
        
        try:
            print(f"📄 Opening CV: {resume.file_path}")
            
            # Open file based on OS
            if platform.system() == 'Windows':
                os.startfile(resume.file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', resume.file_path])
            else:  # Linux
                linux_openers = [
                    'xdg-open', 'gnome-open', 'kde-open',
                    'exo-open', 'gvfs-open', 'firefox'
                ]
                
                opened = False
                for opener in linux_openers:
                    if shutil.which(opener):
                        try:
                            if opener == 'firefox':
                                subprocess.run([opener, f"file://{os.path.abspath(resume.file_path)}"], 
                                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                subprocess.run([opener, resume.file_path], 
                                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            opened = True
                            print(f"✓ Opened with {opener}")
                            break
                        except Exception as e:
                            print(f"⚠️ Failed with {opener}: {e}")
                            continue
                
                if not opened:
                    # Try PDF viewers
                    pdf_viewers = ['evince', 'okular', 'atril', 'mupdf']
                    for viewer in pdf_viewers:
                        if shutil.which(viewer):
                            try:
                                subprocess.run([viewer, resume.file_path], 
                                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                opened = True
                                print(f"✓ Opened with {viewer}")
                                break
                            except Exception as e:
                                continue
                
                if not opened:
                    print("❌ No suitable opener found")
                    print(f"💡 Please install: xdg-open, evince, or firefox")
                    print(f"💡 Manual path: {resume.file_path}")
                    return False
            
            print("✓ CV opened successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error opening CV: {e}")
            return False
    
    def get_resume_info(self, resume_id: str):
        """Get basic resume info"""
        return self.repo.get_resume_by_id(resume_id)
    
    def validate_cv_file(self, resume_id: str) -> bool:
        """Validate CV file exists"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        return os.path.exists(resume.file_path) and os.path.isfile(resume.file_path)
    
    def get_cv_preview(self, resume_id: str, max_length: int = 500) -> Optional[str]:
        """Get CV text preview"""
        cv_text = self.get_cv_text(resume_id)
        if not cv_text:
            return None
        
        if len(cv_text) <= max_length:
            return cv_text
        
        return cv_text[:max_length] + "..."