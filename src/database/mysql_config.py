"""MySQL database configuration"""

import mysql.connector
from mysql.connector import Error
import os

class MySQLConfig:
    """MySQL database configuration"""
    
    def __init__(self):
        # Database connection parameters
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME', 'kaggle_resumes'),
            'user': os.getenv('DB_USER', 'ats_user'),
            'password': os.getenv('DB_PASSWORD', 'StimaSukses'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True,
            'connection_timeout': 10,
            'raise_on_warnings': False
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            connection = mysql.connector.connect(**self.config)
            if connection.is_connected():
                print(f"Connected to MySQL: {self.config['database']}")
                return connection
            return None
        except Error as e:
            print(f"MySQL connection error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            connection = self.get_connection()
            if connection and connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                return result is not None
            return False
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def close_connection(self, connection):
        """Close database connection"""
        try:
            if connection and connection.is_connected():
                connection.close()
                print("MySQL connection closed")
        except Error as e:
            print(f"Error closing connection: {e}")
    
    def execute_query(self, query: str, params=None):
        """Execute query with connection handling"""
        connection = None
        try:
            connection = self.get_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.rowcount
            
            cursor.close()
            return result
            
        except Error as e:
            print(f"Query execution error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if connection:
                self.close_connection(connection)
    
    def get_database_info(self) -> dict:
        """Get database information"""
        try:
            connection = self.get_connection()
            if not connection:
                return {}
            
            cursor = connection.cursor()
            
            # Get version
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # Get table count
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return {
                'version': version,
                'database': self.config['database'],
                'tables': len(tables),
                'host': self.config['host'],
                'port': self.config['port']
            }
            
        except Error as e:
            print(f"Error getting database info: {e}")
            return {}