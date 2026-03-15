"""
Custom authentication provider for FastMCP using DavidOS OAuth tokens.
"""

import logging
from typing import Optional
from fastmcp.server.auth import TokenVerifier
from . import oauth_protocol

logger = logging.getLogger("davidos-mcp")


class DavidOSTokenVerifier(TokenVerifier):
    """
    Custom token verifier for DavidOS OAuth tokens.
    
    Integrates with our existing oauth_protocol module to validate
    Bearer tokens issued by our OAuth server.
    """
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify a bearer token and return user context.
        
        Args:
            token: The bearer token to verify
            
        Returns:
            User context dict if valid, None if invalid
        """
        # Use our existing token validation
        token_data = oauth_protocol.validate_access_token(token)
        
        if not token_data:
            return None
        
        # Return user context in format FastMCP expects
        user = token_data.get('user', {})
        return {
            'sub': user.get('email'),
            'email': user.get('email'),
            'name': user.get('name'),
            'scope': token_data.get('scope', ''),
            'client_id': token_data.get('client_id')
        }
    
    def get_auth_routes(self):
        """
        FastMCP calls this to get OAuth routes.
        We return None since we handle OAuth in the main FastAPI app.
        """
        return None
