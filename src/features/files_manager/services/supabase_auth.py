from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY
from .supabase_client import get_supabase_client
from typing import Dict, Any, Optional

class SupabaseAuthService:
    """
    Service for handling authentication with Supabase
    """
    
    @staticmethod
    def get_client():
        """Returns the Supabase client"""
        return get_supabase_client()
    
    @staticmethod
    async def sign_up(email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data
        """
        client = SupabaseAuthService.get_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        return response
    
    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Session and user data
        """
        client = SupabaseAuthService.get_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    
    @staticmethod
    async def sign_out(jwt: str) -> None:
        """
        Sign out a user
        
        Args:
            jwt: User JWT token
        """
        client = SupabaseAuthService.get_client()
        client.auth.sign_out()
    
    @staticmethod
    async def reset_password(email: str) -> Dict[str, Any]:
        """
        Send password reset email
        
        Args:
            email: User email
            
        Returns:
            Result of operation
        """
        client = SupabaseAuthService.get_client()
        return client.auth.reset_password_for_email(email)
    
    @staticmethod
    async def get_user(jwt: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from JWT
        
        Args:
            jwt: User JWT token
            
        Returns:
            User data or None
        """
        client = SupabaseAuthService.get_client()
        try:
            return client.auth.get_user(jwt)
        except Exception:
            return None
