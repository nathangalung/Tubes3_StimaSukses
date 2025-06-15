"""Repository with encryption support"""

from typing import List, Dict, Optional
import mysql.connector
from mysql.connector import Error
import os
import sys
from pathlib import Path

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

from utils.database_util import DatabaseUtil
from database.models import Resume
from utils.encryption import Encryption

class ResumeRepository:
    """Repository for resume data with encryption support"""
    
    def __init__(self, use_encryption: bool = False):
        self.db_util = DatabaseUtil()
        self.use_encryption = use_encryption
        self.encryptor = Encryption("ATS_Database_Key_2024") if use_encryption else None
    
    def get_all_resumes(self) -> List[Resume]:
        """Get all resumes with optional decryption"""
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
                    ad.detail_id,
                    ap.first_name,
                    ap.last_name
                FROM ApplicationDetail ad
                LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
                ORDER BY ad.detail_id
                LIMIT 1000
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            resumes = []
            for result in results:
                # Handle encryption/decryption
                if self.use_encryption and self.encryptor:
                    decrypted_data = self.encryptor.decrypt_profile_data(result)
                    first_name = decrypted_data.get('first_name', '')
                    last_name = decrypted_data.get('last_name', '')
                    phone = decrypted_data.get('phone_number', result['phone'])
                    address = decrypted_data.get('address', result['address'])
                else:
                    first_name = result['first_name'] or ''
                    last_name = result['last_name'] or ''
                    phone = result['phone']
                    address = result['address']
                
                # Normalize file path
                file_path = result['file_path']
                if file_path:
                    file_path = file_path.replace('\\', '/')
                
                # Construct name
                name = f"{first_name} {last_name}".strip()
                if not name or name == ' ':
                    name = 'Unknown'
                
                resume = Resume(
                    id=result['id'],
                    category=result['category'] or 'Unknown',
                    file_path=file_path,
                    name=name,
                    phone=phone,
                    birthdate=result['birthdate'],
                    address=address
                )
                resumes.append(resume)
            
            cursor.close()
            return resumes
            
        except Error as e:
            print(f"Error fetching resumes: {e}")
            return []
        finally:
            self.db_util.close_connection(conn)
    
    def save_encrypted_profile(self, profile_data: dict) -> bool:
        """Save encrypted profile data to database"""
        if not self.use_encryption or not self.encryptor:
            print("❌ Encryption not enabled")
            return False
        
        conn = self.db_util.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Encrypt sensitive data
            encrypted_data = self.encryptor.encrypt_profile_data(profile_data)
            
            # Insert into database
            insert_query = """
                INSERT INTO ApplicantProfile 
                (first_name, last_name, phone_number, address, date_of_birth)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                encrypted_data.get('first_name', ''),
                encrypted_data.get('last_name', ''),
                encrypted_data.get('phone_number', ''),
                encrypted_data.get('address', ''),
                profile_data.get('date_of_birth')
            ))
            
            conn.commit()
            cursor.close()
            
            print("✅ Encrypted profile saved successfully")
            return True
            
        except Error as e:
            print(f"Error saving encrypted profile: {e}")
            return False
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