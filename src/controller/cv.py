"""CV operations controller with proper WSL path handling"""

import os
import platform
import subprocess
import shutil
import webbrowser
import glob
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
        file_path = self._resolve_cv_path(resume.file_path)
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
        """Open CV file with proper WSL path handling"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"❌ Resume not found: {resume_id}")
            return False
        
        # Resolve file path
        file_path = self._resolve_cv_path(resume.file_path)
        if not file_path:
            print(f"❌ CV file not found: {resume.file_path}")
            return False
        
        print(f"found cv file at: {file_path}")
        print(f"opening cv file: {file_path}")
        
        try:
            # Detect environment and use appropriate method
            if self._is_wsl():
                return self._open_wsl(file_path)
            elif platform.system() == 'Windows':
                return self._open_windows(file_path)
            elif platform.system() == 'Darwin':
                return self._open_macos(file_path)
            else:
                return self._open_linux(file_path)
                
        except Exception as e:
            print(f"❌ Error opening CV: {e}")
            return False
    
    def _resolve_cv_path(self, cv_path: str) -> Optional[str]:
        """Resolve CV path with multiple fallback options"""
        project_root = Path(__file__).parent.parent.parent
        
        # Normalize path separators
        cv_path = cv_path.replace('\\', '/')
        
        # Possible path configurations
        path_options = [
            cv_path,  # Original path
            str(project_root / cv_path),  # Project root + cv_path
            str(project_root / cv_path.replace('data/', '')),  # Remove data prefix
            str(project_root / 'data' / cv_path),  # Add data prefix
            str(project_root / 'data' / os.path.basename(cv_path)),  # Only filename in data
        ]
        
        # Try each path option
        for path in path_options:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        
        # Last resort: search in data directory
        data_dir = project_root / 'data'
        if data_dir.exists():
            filename = os.path.basename(cv_path)
            for root, dirs, files in os.walk(data_dir):
                if filename in files:
                    found_path = os.path.join(root, filename)
                    return found_path
        
        return None
    
    def _is_wsl(self) -> bool:
        """Detect if running in WSL environment"""
        try:
            # Check for WSL-specific indicators
            if os.path.exists('/proc/version'):
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    return 'microsoft' in version_info or 'wsl' in version_info
            
            # Check for WSL mount points
            return os.path.exists('/mnt/c') or os.path.exists('/mnt/d')
        except:
            return False
    
    def _get_windows_path_from_wsl(self, wsl_path: str) -> Optional[str]:
        """Convert WSL path to Windows path or copy file to Windows accessible location"""
        
        # Method 1: If path is already in /mnt/c (Windows file system)
        if wsl_path.startswith('/mnt/c/'):
            # Convert /mnt/c/... to C:\...
            windows_path = wsl_path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
            print(f"converted wsl path: {wsl_path} -> {windows_path}")
            return windows_path
        
        # Method 2: If path is in WSL file system (/home/...), copy to temp Windows location
        if wsl_path.startswith('/home/') or not wsl_path.startswith('/mnt/'):
            try:
                import tempfile
                import shutil
                
                # Get Windows temp directory through WSL
                windows_temp = "/mnt/c/Windows/Temp"
                if not os.path.exists(windows_temp):
                    windows_temp = "/mnt/c/tmp"
                    os.makedirs(windows_temp, exist_ok=True)
                
                # Create unique filename
                import uuid
                filename = os.path.basename(wsl_path)
                temp_filename = f"cv_{uuid.uuid4().hex[:8]}_{filename}"
                temp_wsl_path = os.path.join(windows_temp, temp_filename)
                
                # Copy file from WSL to Windows accessible location
                shutil.copy2(wsl_path, temp_wsl_path)
                
                # Convert temp path to Windows format
                windows_path = temp_wsl_path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
                print(f"copied wsl file to windows: {wsl_path} -> {windows_path}")
                return windows_path
                
            except Exception as e:
                print(f"⚠️ Failed to copy file to Windows location: {e}")
                return None
        
        return None
    
    def _open_wsl(self, file_path: str) -> bool:
        """Open file in WSL environment with proper path conversion"""
        try:
            # Convert to Windows accessible path
            windows_path = self._get_windows_path_from_wsl(file_path)
            if not windows_path:
                print("❌ Could not convert WSL path to Windows path")
                return False
            
            # Method 1: Try PowerShell with Windows path
            try:
                escaped_path = windows_path.replace("'", "''")
                powershell_cmd = f"Start-Process -FilePath '{escaped_path}'"
                result = subprocess.run(['powershell.exe', '-Command', powershell_cmd],
                                      capture_output=True,
                                      text=True,
                                      timeout=10)
                
                if result.returncode == 0:
                    print("opened with powershell.exe")
                    return True
                else:
                    print(f"⚠️ powershell.exe failed with code {result.returncode}: {result.stderr.strip()}")
                    
            except subprocess.TimeoutExpired:
                print("opened with powershell.exe (timeout but likely successful)")
                return True
            except Exception as e:
                print(f"⚠️ powershell.exe failed: {e}")
            
            # Method 2: Try cmd.exe with Windows path
            try:
                cmd = ['cmd.exe', '/c', 'start', '""', f'"{windows_path}"']
                result = subprocess.run(cmd, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                if result.returncode == 0:
                    print("opened with cmd.exe")
                    return True
                else:
                    print(f"⚠️ cmd.exe failed with code {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                print("opened with cmd.exe (timeout but likely successful)")
                return True
            except Exception as e:
                print(f"⚠️ cmd.exe failed: {e}")
            
            # Method 3: Try Chrome with file URL
            try:
                file_url = f"file:///{windows_path.replace(chr(92), '/')}"
                
                # Find Chrome installation
                chrome_paths = [
                    '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
                    '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
                ]
                
                # Try user-specific Chrome installations
                user_chrome_pattern = '/mnt/c/Users/*/AppData/Local/Google/Chrome/Application/chrome.exe'
                chrome_paths.extend(glob.glob(user_chrome_pattern))
                
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        subprocess.run([chrome_path, file_url], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     timeout=5)
                        print(f"opened with chrome: {chrome_path}")
                        return True
                        
            except Exception as e:
                print(f"⚠️ Chrome failed: {e}")
            
            # Method 4: Try Edge browser
            try:
                edge_paths = [
                    '/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                    '/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe'
                ]
                
                file_url = f"file:///{windows_path.replace(chr(92), '/')}"
                
                for edge_path in edge_paths:
                    if os.path.exists(edge_path):
                        subprocess.run([edge_path, file_url],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     timeout=5)
                        print(f"opened with edge: {edge_path}")
                        return True
                        
            except Exception as e:
                print(f"⚠️ Edge failed: {e}")
            
            # Method 5: Try explorer.exe
            try:
                result = subprocess.run(['explorer.exe', windows_path],
                                      capture_output=True,
                                      text=True,
                                      timeout=10)
                if result.returncode == 0:
                    print("opened with explorer.exe")
                    return True
            except Exception as e:
                print(f"⚠️ Explorer failed: {e}")
            
            print("❌ All WSL opening methods failed")
            print(f"💡 Manual path: {windows_path}")
            return False
            
        except Exception as e:
            print(f"❌ WSL opening error: {e}")
            return False
    
    def _open_windows(self, file_path: str) -> bool:
        """Open file on Windows"""
        try:
            # Method 1: os.startfile
            os.startfile(file_path)
            print("opened with windows default app")
            return True
        except Exception as e:
            print(f"⚠️ startfile failed: {e}")
            
            try:
                # Method 2: subprocess with start command
                subprocess.run(['cmd', '/c', 'start', '""', f'"{file_path}"'], 
                             check=True, shell=True)
                print("opened with cmd start")
                return True
            except Exception as e2:
                print(f"⚠️ cmd start failed: {e2}")
                
                try:
                    # Method 3: webbrowser module
                    file_url = f"file:///{file_path.replace(os.sep, '/')}"
                    webbrowser.open(file_url)
                    print("opened with webbrowser")
                    return True
                except Exception as e3:
                    print(f"❌ All Windows methods failed: {e3}")
                    return False
    
    def _open_macos(self, file_path: str) -> bool:
        """Open file on macOS"""
        try:
            subprocess.run(['open', file_path], check=True, timeout=10)
            print("opened with macos default app")
            return True
        except Exception as e:
            print(f"❌ macOS open failed: {e}")
            return False
    
    def _open_linux(self, file_path: str) -> bool:
        """Open file on Linux"""
        file_url = f"file://{file_path}"
        
        # Method 1: xdg-open
        if shutil.which('xdg-open'):
            try:
                subprocess.run(['xdg-open', file_path], 
                             check=True, 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=10)
                print("opened with xdg-open")
                return True
            except Exception as e:
                print(f"⚠️ xdg-open failed: {e}")
        
        # Method 2: Try browsers
        browsers = ['google-chrome', 'chromium-browser', 'firefox', 'chromium']
        for browser in browsers:
            if shutil.which(browser):
                try:
                    subprocess.run([browser, file_url], 
                                 check=False,
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL,
                                 timeout=10)
                    print(f"opened with {browser}")
                    return True
                except Exception:
                    continue
        
        # Method 3: PDF viewers
        pdf_viewers = ['evince', 'okular', 'atril', 'zathura', 'mupdf']
        for viewer in pdf_viewers:
            if shutil.which(viewer):
                try:
                    subprocess.run([viewer, file_path], 
                                 check=False,
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL,
                                 timeout=10)
                    print(f"opened with {viewer}")
                    return True
                except Exception:
                    continue
        
        print("❌ No suitable Linux PDF viewer found")
        return False
    
    def get_resume_info(self, resume_id: str):
        """Get basic resume info"""
        return self.repo.get_resume_by_id(resume_id)
    
    def validate_cv_file(self, resume_id: str) -> bool:
        """Validate CV file exists"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        return self._resolve_cv_path(resume.file_path) is not None
    
    def get_cv_preview(self, resume_id: str, max_length: int = 500) -> Optional[str]:
        """Get CV text preview"""
        cv_text = self.get_cv_text(resume_id)
        if not cv_text:
            return None
        
        if len(cv_text) <= max_length:
            return cv_text
        
        return cv_text[:max_length] + "..."