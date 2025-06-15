"""CV operations controller"""

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
        print(f"📋 Generating summary for {resume_id}")
        
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"❌ Resume {resume_id} not found")
            return None
        
        # Resolve file path
        file_path = self._resolve_file_path(resume.file_path)
        if not file_path:
            print(f"❌ File not found: {resume.file_path}")
            return None
        
        # Extract text
        cv_text = self.pdf_extractor.extract_text(file_path)
        if not cv_text:
            print(f"❌ Failed to extract text from {file_path}")
            return None
        
        print(f"✅ Extracted {len(cv_text)} characters")
        
        # Extract summary using regex
        summary = self.regex_extractor.extract_summary(cv_text)
        
        # Enhance with database info
        if resume.name and resume.name.lower() != "unknown":
            summary.name = resume.name
        if resume.phone:
            summary.contact_info['phone'] = resume.phone
        if resume.address:
            summary.contact_info['address'] = resume.address
        
        print(f"✅ Generated summary: {len(summary.skills)} skills, {len(summary.job_history)} jobs")
        
        return summary
    
    def open_cv_file(self, resume_id: str) -> bool:
        """Open CV file with cross-platform support"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"❌ Resume not found: {resume_id}")
            return False
        
        # Resolve file path
        file_path = self._resolve_file_path(resume.file_path)
        if not file_path:
            print(f"❌ CV file not found: {resume.file_path}")
            return False
        
        print(f"📄 Opening CV: {file_path}")
        
        try:
            current_platform = platform.system()
            
            if current_platform == 'Windows':
                return self._open_windows(file_path)
            elif current_platform == 'Darwin':  # macOS
                return self._open_macos(file_path)
            else:  # Linux and other Unix-like systems
                return self._open_linux(file_path)
                
        except Exception as e:
            print(f"❌ Error opening CV: {e}")
            return False
    
    def _resolve_file_path(self, file_path: str) -> Optional[str]:
        """Resolve file path to absolute path"""
        # Convert to Path object for better handling
        path = Path(file_path)
        
        # If already absolute and exists
        if path.is_absolute() and path.exists():
            return str(path.resolve())
        
        # Try relative to project root
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path
        
        if full_path.exists():
            return str(full_path.resolve())
        
        # Try with forward slashes (Windows compatibility)
        normalized_path = project_root / file_path.replace('\\', '/')
        if normalized_path.exists():
            return str(normalized_path.resolve())
        
        return None
    
    def _open_windows(self, file_path: str) -> bool:
        """Open file on Windows"""
        try:
            # Method 1: os.startfile (most reliable on Windows)
            os.startfile(file_path)
            print("✅ Opened with Windows default app")
            return True
        except Exception as e:
            print(f"⚠️ os.startfile failed: {e}")
            
        try:
            # Method 2: subprocess with cmd
            subprocess.run(['cmd', '/c', 'start', '', file_path], 
                         check=True, shell=True)
            print("✅ Opened with cmd start")
            return True
        except Exception as e:
            print(f"⚠️ cmd start failed: {e}")
            
        try:
            # Method 3: PowerShell Invoke-Item
            subprocess.run(['powershell', 'Invoke-Item', f'"{file_path}"'], 
                         check=True)
            print("✅ Opened with PowerShell")
            return True
        except Exception as e:
            print(f"⚠️ PowerShell failed: {e}")
            
        # Method 4: Try common Windows PDF viewers
        pdf_viewers = [
            'AcroRd32.exe',  # Adobe Reader
            'Acrobat.exe',   # Adobe Acrobat
            'msedge.exe',    # Microsoft Edge
            'chrome.exe',    # Google Chrome
            'firefox.exe'    # Firefox
        ]
        
        for viewer in pdf_viewers:
            try:
                subprocess.run([viewer, file_path], 
                             check=True, timeout=10,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                print(f"✅ Opened with {viewer}")
                return True
            except:
                continue
        
        print("❌ No Windows PDF viewer found")
        print(f"💡 Manual path: {file_path}")
        return False
    
    def _open_macos(self, file_path: str) -> bool:
        """Open file on macOS"""
        try:
            subprocess.run(['open', file_path], check=True, timeout=10)
            print("✅ Opened with macOS default app")
            return True
        except Exception as e:
            print(f"❌ macOS open failed: {e}")
            return False
    
    def _open_linux(self, file_path: str) -> bool:
        """Open file on Linux"""
        # Method 1: xdg-open (most reliable)
        if shutil.which('xdg-open'):
            try:
                subprocess.run(['xdg-open', file_path], 
                             check=True, timeout=10,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                print("✅ Opened with xdg-open")
                return True
            except:
                pass
        
        # Method 2: Try browsers with file:// protocol
        browsers = ['firefox', 'google-chrome', 'chromium-browser', 'chromium']
        file_url = f"file://{file_path}"
        
        for browser in browsers:
            if shutil.which(browser):
                try:
                    subprocess.run([browser, file_url], 
                                 check=False, timeout=10,
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                    print(f"✅ Opened with {browser}")
                    return True
                except:
                    continue
        
        # Method 3: Try PDF viewers
        pdf_viewers = ['evince', 'okular', 'atril', 'zathura', 'mupdf']
        
        for viewer in pdf_viewers:
            if shutil.which(viewer):
                try:
                    subprocess.run([viewer, file_path], 
                                 check=False, timeout=10,
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                    print(f"✅ Opened with {viewer}")
                    return True
                except:
                    continue
        
        print("❌ No Linux PDF viewer found")
        print("💡 Install: xdg-open, firefox, or evince")
        print(f"💡 Manual path: {file_path}")
        return False
    
    def get_resume_info(self, resume_id: str):
        """Get basic resume info"""
        return self.repo.get_resume_by_id(resume_id)
    
    def validate_cv_file(self, resume_id: str) -> bool:
        """Validate CV file exists"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        return self._resolve_file_path(resume.file_path) is not None
    
    def get_cv_preview(self, resume_id: str, max_length: int = 500) -> Optional[str]:
        """Get CV text preview"""
        cv_text = self.get_cv_text(resume_id)
        if not cv_text:
            return None
        
        if len(cv_text) <= max_length:
            return cv_text
        
        return cv_text[:max_length] + "..."