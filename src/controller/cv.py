"""cv operations controller"""

import os
import platform
import subprocess
import shutil
import webbrowser
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
        """open cv file dengan path resolution yang diperbaiki"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            print(f"resume not found: {resume_id}")
            return False
        
        # resolve file path dengan multiple fallback options
        file_path = self._resolve_cv_path(resume.file_path)
        
        if not file_path:
            print(f"cv file not found for resume {resume_id}")
            print(f"original path: {resume.file_path}")
            return False
        
        try:
            print(f"opening cv file: {file_path}")
            
            # convert to absolute path dan normalize
            file_path = os.path.abspath(file_path)
            
            # detect wsl environment
            if self._is_wsl():
                return self._open_wsl(file_path)
            
            # open berdasarkan platform dengan fallback options
            if platform.system() == 'Windows':
                return self._open_windows(file_path)
            elif platform.system() == 'Darwin':
                return self._open_macos(file_path)
            else:
                return self._open_linux(file_path)
                
        except Exception as e:
            print(f"error opening cv: {e}")
            return False
    
    def _resolve_cv_path(self, cv_path: str) -> Optional[str]:
        """resolve cv path dengan multiple fallback options"""
        project_root = Path(__file__).parent.parent.parent
        
        # possible path configurations
        path_options = [
            cv_path,  # original path
            os.path.join(project_root, cv_path),  # project root + cv_path
            os.path.join(project_root, cv_path.replace('data/', '')),  # remove data prefix
            os.path.join(project_root, 'data', cv_path),  # add data prefix
            os.path.join(project_root, 'data', os.path.basename(cv_path)),  # only filename in data
        ]
        
        # try each path option
        for path in path_options:
            if os.path.exists(path) and os.path.isfile(path):
                print(f"found cv file at: {path}")
                return path
        
        # last resort: search in data directory
        data_dir = project_root / 'data'
        if data_dir.exists():
            filename = os.path.basename(cv_path)
            for root, dirs, files in os.walk(data_dir):
                if filename in files:
                    found_path = os.path.join(root, filename)
                    print(f"found cv file by search: {found_path}")
                    return found_path
        
        return None
    
    def _is_wsl(self) -> bool:
        """detect if running in wsl environment"""
        try:
            # check for wsl-specific indicators
            if os.path.exists('/proc/version'):
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    return 'microsoft' in version_info or 'wsl' in version_info
            
            # check for wsl mount points
            return os.path.exists('/mnt/c') or os.path.exists('/mnt/d')
        except:
            return False
    
    def _wsl_to_windows_path(self, wsl_path: str) -> str:
        """convert wsl path to windows path"""
        # convert /mnt/c/Users/... to C:\Users\...
        if wsl_path.startswith('/mnt/'):
            # extract drive letter and path
            parts = wsl_path.split('/')
            if len(parts) >= 3:
                drive = parts[2].upper()
                remaining_path = '/'.join(parts[3:])
                windows_path = f"{drive}:\\{remaining_path.replace('/', '\\')}"
                print(f"converted wsl path: {wsl_path} -> {windows_path}")
                return windows_path
        
        return wsl_path
    
    def _open_wsl(self, file_path: str) -> bool:
        """open file in wsl environment using windows commands"""
        try:
            # convert wsl path to windows path
            windows_path = self._wsl_to_windows_path(file_path)
            
            # method 1: use powershell (most reliable for paths with spaces)
            try:
                # escape path properly for powershell
                escaped_path = windows_path.replace("'", "''")
                powershell_cmd = f"Start-Process -FilePath '{escaped_path}'"
                subprocess.run([
                    'powershell.exe', '-Command', powershell_cmd
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                print("opened with powershell.exe")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"powershell.exe failed: {e}")
            
            # method 2: try to open with chrome directly
            try:
                # convert windows path to file url
                file_url = f"file:///{windows_path.replace(chr(92), '/')}"  # replace backslash
                chrome_paths = [
                    '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
                    '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
                    '/mnt/c/Users/*/AppData/Local/Google/Chrome/Application/chrome.exe'
                ]
                
                for chrome_path in chrome_paths:
                    if '*' in chrome_path:
                        # expand wildcard for user-specific chrome
                        import glob
                        matching_paths = glob.glob(chrome_path)
                        for match in matching_paths:
                            if os.path.exists(match):
                                subprocess.run([
                                    match, file_url
                                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                print(f"opened with chrome: {match}")
                                return True
                    elif os.path.exists(chrome_path):
                        subprocess.run([
                            chrome_path, file_url
                        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"opened with chrome: {chrome_path}")
                        return True
            except Exception as e:
                print(f"chrome direct failed: {e}")
            
            # method 3: use cmd.exe with proper escaping
            try:
                # use 8.3 short name to avoid space issues
                short_path_cmd = f'for %i in ("{windows_path}") do start "" "%~si"'
                subprocess.run([
                    'cmd.exe', '/c', short_path_cmd
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                print("opened with cmd.exe using short path")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"cmd.exe with short path failed: {e}")
            
            # method 4: use wsl-open if available
            try:
                if shutil.which('wsl-open'):
                    subprocess.run([
                        'wsl-open', windows_path
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                    print("opened with wsl-open")
                    return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"wsl-open failed: {e}")
            
            # method 5: fallback to python webbrowser with file url
            try:
                file_url = f"file:///{windows_path.replace(chr(92), '/')}"
                webbrowser.open(file_url)
                print("opened with python webbrowser")
                return True
            except Exception as e:
                print(f"python webbrowser failed: {e}")
            
            print("all wsl opening methods failed")
            return False
            
        except Exception as e:
            print(f"wsl opening error: {e}")
            return False
    
    def _open_windows(self, file_path: str) -> bool:
        """open file on windows"""
        try:
            # method 1: os.startfile (default app)
            os.startfile(file_path)
            print("opened with windows default app")
            return True
        except Exception as e:
            print(f"startfile failed: {e}")
            
            try:
                # method 2: webbrowser module
                file_url = f"file:///{file_path.replace(os.sep, '/')}"
                webbrowser.open(file_url)
                print("opened with webbrowser")
                return True
            except Exception as e2:
                print(f"webbrowser failed: {e2}")
                return False
    
    def _open_macos(self, file_path: str) -> bool:
        """open file on macos"""
        try:
            subprocess.run(['open', file_path], check=True)
            print("opened with macos default app")
            return True
        except subprocess.CalledProcessError as e:
            print(f"macos open failed: {e}")
            return False
    
    def _open_linux(self, file_path: str) -> bool:
        """open file on linux with multiple fallback options"""
        file_url = f"file://{file_path}"
        
        # method 1: xdg-open
        if shutil.which('xdg-open'):
            try:
                subprocess.run(['xdg-open', file_path], 
                             check=True, 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=10)
                print("opened with xdg-open")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"xdg-open failed: {e}")
        
        # method 2: try browsers
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
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
        
        # method 3: webbrowser module
        try:
            webbrowser.open(file_url)
            print("opened with python webbrowser")
            return True
        except Exception as e:
            print(f"webbrowser failed: {e}")
        
        # method 4: pdf viewers
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
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
        
        print("no suitable application found for opening pdf")
        return False
    
    def get_resume_info(self, resume_id: str):
        """get basic resume info"""
        return self.repo.get_resume_by_id(resume_id)
    
    def validate_cv_file(self, resume_id: str) -> bool:
        """validate cv file exists"""
        resume = self.repo.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        return self._resolve_cv_path(resume.file_path) is not None
    
    def get_cv_preview(self, resume_id: str, max_length: int = 500) -> Optional[str]:
        """get cv text preview"""
        cv_text = self.get_cv_text(resume_id)
        if not cv_text:
            return None
        
        if len(cv_text) <= max_length:
            return cv_text
        
        return cv_text[:max_length] + "..."