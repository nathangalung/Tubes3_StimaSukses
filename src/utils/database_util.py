"""Database utility functions"""

from database.mysql_config import MySQLConfig

class DatabaseUtil:
    """Database utility wrapper"""
    
    def __init__(self):
        self.mysql_config = MySQLConfig()
    
    def get_connection(self):
        """Get database connection"""
        return self.mysql_config.get_connection()
    
    def test_connection(self):
        """Test database connection"""
        return self.mysql_config.test_connection()
    
    def close_connection(self, connection):
        """Close database connection"""
        return self.mysql_config.close_connection(connection)
    
    def execute_query(self, query: str, params=None):
        """Execute query"""
        return self.mysql_config.execute_query(query, params)
    
    def get_database_info(self):
        """Get database info"""
        return self.mysql_config.get_database_info()