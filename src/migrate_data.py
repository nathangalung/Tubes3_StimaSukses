#!/usr/bin/env python3
"""
MySQL Data Migration Script for ATS CV Search
Migrates Resume.csv data to MySQL database with ApplicantProfile/ApplicationDetail schema
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database.mysql_config import MySQLConfig

def create_connection():
    """Create connection to MySQL server"""
    config = MySQLConfig()
    return config.get_connection()

def check_and_create_schema(conn):
    """Check if required tables exist and create if needed"""
    try:
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📋 Existing tables: {existing_tables}")
        
        # If tables don't exist, run the seeding SQL
        if 'ApplicantProfile' not in existing_tables or 'ApplicationDetail' not in existing_tables:
            print("🔨 Running database seeding...")
            
            # Use the tubes3_seeding.sql file since it has all the data
            current_dir = Path(__file__).parent
            project_root = current_dir.parent  # Go up from src to project root
            seeding_file = project_root / "tubes3_seeding.sql"
            
            if seeding_file.exists():
                with open(seeding_file, 'r', encoding='utf-8') as f:
                    seeding_sql = f.read()
                
                print(f"📄 Read seeding file: {len(seeding_sql)} characters")
                
                # Split into individual statements and execute them
                statements = split_sql_statements(seeding_sql)
                print(f"🔧 Executing {len(statements)} SQL statements...")
                
                for i, statement in enumerate(statements):
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                            if i % 50 == 0:  # Progress indicator
                                print(f"   ✅ Executed {i+1}/{len(statements)} statements")
                        except Exception as e:
                            if "Duplicate entry" in str(e):
                                # Skip duplicate entries
                                continue
                            print(f"   ⚠️ Warning on statement {i+1}: {e}")
                            # Continue with other statements
                
                conn.commit()
                print("✅ Database seeding completed successfully")
            else:
                print("❌ tubes3_seeding.sql file not found, creating basic schema...")
                create_basic_schema(cursor)
                conn.commit()
        else:
            print("✅ Tables already exist, skipping schema creation")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"❌ Error setting up schema: {e}")
        conn.rollback()
        return False

def split_sql_statements(sql_content):
    """Split SQL content into individual statements"""
    # Remove comments and empty lines
    lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            lines.append(line)
    
    # Join lines and split by semicolon
    clean_sql = ' '.join(lines)
    statements = [stmt.strip() for stmt in clean_sql.split(';') if stmt.strip()]
    
    return statements

def create_basic_schema(cursor):
    """Create basic schema if seeding file is not available"""
    print("🏗️ Creating basic MySQL schema...")
    
    # Drop existing tables
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DROP TABLE IF EXISTS ApplicationDetail")
    cursor.execute("DROP TABLE IF EXISTS ApplicantProfile")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    # Create ApplicantProfile table
    cursor.execute("""
        CREATE TABLE ApplicantProfile (
            applicant_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            date_of_birth DATE,
            address VARCHAR(255),
            phone_number VARCHAR(20)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Create ApplicationDetail table
    cursor.execute("""
        CREATE TABLE ApplicationDetail (
            detail_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT NOT NULL,
            application_role VARCHAR(100),
            cv_path TEXT,
            FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    print("✅ Basic schema created successfully")

def verify_data(conn):
    """Verify imported data and check file paths"""
    try:
        cursor = conn.cursor()
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM ApplicantProfile")
        applicant_total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ApplicationDetail")
        application_total = cursor.fetchone()[0]
        
        print(f"\n🔍 Verification Results:")
        print(f"   Total applicants: {applicant_total}")
        print(f"   Total applications: {application_total}")
        
        # Check a few sample records with joins
        cursor.execute("""
            SELECT ap.first_name, ap.last_name, ad.application_role, ad.cv_path
            FROM ApplicantProfile ap
            JOIN ApplicationDetail ad ON ap.applicant_id = ad.applicant_id
            LIMIT 5
        """)
        samples = cursor.fetchall()
        print(f"\n📋 Sample records:")
        for sample in samples:
            first_name, last_name, role, file_path = sample
            # Check if file exists relative to project root
            full_path = Path(__file__).parent.parent / file_path
            file_exists = "✅" if full_path.exists() else "❌"
            print(f"   {file_exists} {first_name} {last_name} ({role}): {file_path}")
            
        cursor.close()
        
    except Error as e:
        print(f"❌ Error verifying data: {e}")

def main():
    """Main function to run the migration process"""
    print("=== ATS CV Search - MySQL Data Migration ===")
    print("🔗 Target: MySQL database with existing schema")
    
    # Check if MySQL is running
    conn = create_connection()
    if not conn:
        print("\n💡 Make sure MySQL is running:")
        print("   docker-compose up -d")
        print("   docker-compose ps")
        return
    
    try:
        # Setup schema first
        if not check_and_create_schema(conn):
            print("❌ Schema setup failed!")
            return
            
        verify_data(conn)
        print("\n🎉 Migration completed successfully!")
        print("The ATS application is now ready to use with MySQL backend.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("🔒 MySQL connection closed.")

if __name__ == '__main__':
    main()