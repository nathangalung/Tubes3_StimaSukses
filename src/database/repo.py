"""Repository for resume data"""

from typing import List, Dict, Optional
import mysql.connector
from mysql.connector import Error
import os
import sys

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

from utils.database_util import DatabaseUtil
from database.models import Resume

class ResumeRepository:
    """Repository for resume data"""
    
    def __init__(self):
        self.db_util = DatabaseUtil()
    
    def get_all_resumes(self) -> List[Resume]:
        """Get all resumes"""
        conn = self.db_util.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Join tables query
            query = """
                SELECT 
                    CONCAT('CV', LPAD(ad.detail_id, 6, '0')) as id,
                    COALESCE(ad.application_role, 'Unknown') as category,
                    ad.cv_path as file_path,
                    CONCAT(COALESCE(ap.first_name, ''), ' ', COALESCE(ap.last_name, '')) as name,
                    ap.phone_number as phone,
                    ap.date_of_birth as birthdate,
                    ap.address,
                    ad.application_role,
                    ap.applicant_id,
                    ad.detail_id
                FROM ApplicationDetail ad
                LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
                ORDER BY ad.detail_id
                LIMIT 1000
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert to Resume objects
            resumes = []
            for result in results:
                # Clean name
                name = result['name'].strip() if result['name'] else 'Unknown'
                if not name or name == ' ':
                    name = 'Unknown'
                
                # Create Resume object
                resume = Resume(
                    id=result['id'],
                    category=result['category'] or 'Unknown',
                    file_path=result['file_path'],
                    name=name,
                    phone=result['phone'],
                    birthdate=result['birthdate'],
                    address=result['address']
                )
                resumes.append(resume)
            
            cursor.close()
            return resumes
            
        except Error as e:
            print(f"Error fetching resumes: {e}")
            return []
        finally:
            self.db_util.close_connection(conn)
    
    def search_resumes_by_category(self, category: str) -> List[Resume]:
        """Search resumes by category"""
        conn = self.db_util.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    CONCAT('CV', LPAD(ad.detail_id, 6, '0')) as id,
                    COALESCE(ad.application_role, 'Unknown') as category,
                    ad.cv_path as file_path,
                    CONCAT(COALESCE(ap.first_name, ''), ' ', COALESCE(ap.last_name, '')) as name,
                    ap.phone_number as phone,
                    ap.date_of_birth as birthdate,
                    ap.address,
                    ad.application_role,
                    ap.applicant_id,
                    ad.detail_id
                FROM ApplicationDetail ad
                LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
                WHERE ad.application_role LIKE %s
                ORDER BY ad.detail_id
                LIMIT 1000
            """
            
            cursor.execute(query, (f"%{category}%",))
            results = cursor.fetchall()
            
            # Convert to Resume objects
            resumes = []
            for result in results:
                name = result['name'].strip() if result['name'] else 'Unknown'
                if not name or name == ' ':
                    name = 'Unknown'
                
                resume = Resume(
                    id=result['id'],
                    category=result['category'] or 'Unknown',
                    file_path=result['file_path'],
                    name=name,
                    phone=result['phone'],
                    birthdate=result['birthdate'],
                    address=result['address']
                )
                resumes.append(resume)
            
            cursor.close()
            return resumes
            
        except Error as e:
            print(f"Error searching resumes: {e}")
            return []
        finally:
            self.db_util.close_connection(conn)
    
    def get_resume_by_id(self, resume_id: str) -> Optional[Resume]:
        """Get resume by ID"""
        conn = self.db_util.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Extract detail_id from resume_id
            if resume_id.startswith('CV'):
                detail_id = int(resume_id[2:])
            else:
                detail_id = int(resume_id)
            
            query = """
                SELECT 
                    CONCAT('CV', LPAD(ad.detail_id, 6, '0')) as id,
                    COALESCE(ad.application_role, 'Unknown') as category,
                    ad.cv_path as file_path,
                    CONCAT(COALESCE(ap.first_name, ''), ' ', COALESCE(ap.last_name, '')) as name,
                    ap.phone_number as phone,
                    ap.date_of_birth as birthdate,
                    ap.address,
                    ad.application_role,
                    ap.applicant_id,
                    ad.detail_id
                FROM ApplicationDetail ad
                LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
                WHERE ad.detail_id = %s
            """
            
            cursor.execute(query, (detail_id,))
            result = cursor.fetchone()
            
            if result:
                name = result['name'].strip() if result['name'] else 'Unknown'
                if not name or name == ' ':
                    name = 'Unknown'
                
                resume = Resume(
                    id=result['id'],
                    category=result['category'] or 'Unknown',
                    file_path=result['file_path'],
                    name=name,
                    phone=result['phone'],
                    birthdate=result['birthdate'],
                    address=result['address']
                )
                
                cursor.close()
                return resume
            
            cursor.close()
            return None
            
        except (Error, ValueError) as e:
            print(f"Error fetching resume {resume_id}: {e}")
            return None
        finally:
            self.db_util.close_connection(conn)
    
    def get_categories(self) -> List[str]:
        """Get all categories"""
        conn = self.db_util.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT application_role
                FROM ApplicationDetail
                WHERE application_role IS NOT NULL
                ORDER BY application_role
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            categories = [row[0] for row in results if row[0]]
            
            cursor.close()
            return categories
            
        except Error as e:
            print(f"Error fetching categories: {e}")
            return []
        finally:
            self.db_util.close_connection(conn)
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.db_util.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Count applicants
            cursor.execute("SELECT COUNT(*) FROM ApplicantProfile")
            applicant_count = cursor.fetchone()[0]
            
            # Count applications
            cursor.execute("SELECT COUNT(*) FROM ApplicationDetail")
            application_count = cursor.fetchone()[0]
            
            # Count by role
            cursor.execute("""
                SELECT application_role, COUNT(*) 
                FROM ApplicationDetail 
                WHERE application_role IS NOT NULL 
                GROUP BY application_role 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            top_roles = cursor.fetchall()
            
            cursor.close()
            
            return {
                'total_applicants': applicant_count,
                'total_applications': application_count,
                'top_roles': top_roles
            }
            
        except Error as e:
            print(f"Error fetching stats: {e}")
            return {}
        finally:
            self.db_util.close_connection(conn)