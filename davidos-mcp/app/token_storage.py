"""Simple file-based token storage for Railway persistence."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("davidos-mcp")

# Token storage file path
TOKEN_FILE = Path("/tmp/oauth_tokens.json")


def _load_tokens() -> Dict[str, Dict[str, Any]]:
    """Load tokens from file."""
    if not TOKEN_FILE.exists():
        return {}
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            # Clean up expired tokens
            now = datetime.now().timestamp() * 1000
            return {
                token: info for token, info in data.items()
                if info.get('expires_at', 0) > now
            }
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return {}


def _save_tokens(tokens: Dict[str, Dict[str, Any]]):
    """Save tokens to file."""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)
    except Exception as e:
        logger.error(f"Error saving tokens: {e}")


def store_access_token(token: str, user: Dict[str, Any], scope: str, client_id: str, expires_in: int = 3600):
    """Store an access token."""
    tokens = _load_tokens()
    tokens[token] = {
        'user': user,
        'scope': scope,
        'client_id': client_id,
        'expires_at': (datetime.now() + timedelta(seconds=expires_in)).timestamp() * 1000
    }
    _save_tokens(tokens)
    logger.info(f"Stored access token for {user.get('email')}: {token[:10]}...")


def get_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Get token data if valid."""
    tokens = _load_tokens()
    token_data = tokens.get(token)
    
    if not token_data:
        return None
    
    # Check expiration
    if token_data.get('expires_at', 0) < datetime.now().timestamp() * 1000:
        logger.info(f"Token expired: {token[:10]}...")
        return None
    
    return token_data


def store_auth_code(code: str, data: Dict[str, Any]):
    """Store authorization code."""
    codes_file = Path("/tmp/oauth_codes.json")
    
    try:
        codes = {}
        if codes_file.exists():
            with open(codes_file, 'r') as f:
                codes = json.load(f)
        
        codes[code] = data
        
        with open(codes_file, 'w') as f:
            json.dump(codes, f)
        
        logger.info(f"Stored auth code: {code[:10]}...")
    except Exception as e:
        logger.error(f"Error storing auth code: {e}")


def get_auth_code(code: str) -> Optional[Dict[str, Any]]:
    """Get and delete authorization code."""
    codes_file = Path("/tmp/oauth_codes.json")
    
    try:
        if not codes_file.exists():
            return None
        
        with open(codes_file, 'r') as f:
            codes = json.load(f)
        
        code_data = codes.pop(code, None)
        
        if code_data:
            # Check expiration
            if code_data.get('expires_at', 0) < datetime.now().timestamp() * 1000:
                logger.info(f"Auth code expired: {code[:10]}...")
                return None
            
            # Save updated codes (without the used one)
            with open(codes_file, 'w') as f:
                json.dump(codes, f)
        
        return code_data
    except Exception as e:
        logger.error(f"Error getting auth code: {e}")
        return None
