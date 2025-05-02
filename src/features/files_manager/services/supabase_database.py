from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY
from .supabase_client import get_supabase_client
from typing import Dict, List, Any, Optional

class SupabaseDatabaseService:
    """
    Service for handling database operations with Supabase
    """
    
    @staticmethod
    def get_client():
        """Returns the Supabase client"""
        return get_supabase_client()
    
    @staticmethod
    async def select(
        table: str,
        columns: str = "*", 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        ascending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Select data from a Supabase table
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Optional dict of filters
            limit: Optional result limit
            order: Optional column to order by
            ascending: Whether to order ascending (default: True)
            
        Returns:
            List of records
        """
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
                
        if order:
            if ascending:
                query = query.order(order)
            else:
                query = query.order(order, desc=True)
                
        if limit:
            query = query.limit(limit)
            
        response = query.execute()
        return response.data
    
    @staticmethod
    async def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert data into a Supabase table
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted record
        """
        client = SupabaseDatabaseService.get_client()
        response = client.table(table).insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    async def update(
        table: str, 
        data: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Update data in a Supabase table
        
        Args:
            table: Table name
            data: Data to update
            filters: Filters to identify rows to update
            
        Returns:
            Updated records
        """
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
            
        response = query.execute()
        return response.data
    
    @staticmethod
    async def delete(table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete data from a Supabase table
        
        Args:
            table: Table name
            filters: Filters to identify rows to delete
            
        Returns:
            Deleted records
        """
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
            
        response = query.execute()
        return response.data
