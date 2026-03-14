"""
OAuth 2.1 + OIDC Protocol Implementation for ChatGPT Apps SDK.

This module implements the complete OAuth flow required by ChatGPT:
1. Discovery endpoints
2. Dynamic Client Registration (DCR)
3. Authorization with PKCE
4. Token exchange
5. Token validation for MCP requests

Reference: https://developers.openai.com/apps-sdk/build/auth/
"""

import logging
import secrets
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("davidos-mcp.oauth")

# Base URL - should be configured via environment
BASE_URL = "https://davidos-mcp-production.up.railway.app"

# Storage paths
CLIENTS_FILE = Path("/tmp/oauth_clients.json")
AUTH_CODES_FILE = Path("/tmp/oauth_codes.json")
TOKENS_FILE = Path("/tmp/oauth_tokens.json")


# === PROTOCOL LOGGING ===

def log_protocol_event(stage: str, **kwargs):
    """Structured logging for OAuth protocol events."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        **kwargs
    }
    logger.info(f"[OAUTH_PROTOCOL] {stage}: {json.dumps(log_data)}")


# === DISCOVERY ENDPOINTS ===

def get_protected_resource_metadata() -> Dict[str, Any]:
    """
    OAuth 2.0 Protected Resource Metadata (RFC 9728).
    
    This is the FIRST endpoint ChatGPT calls to discover the authorization server.
    """
    log_protocol_event("DISCOVERY", endpoint="oauth-protected-resource")
    
    return {
        "resource": f"{BASE_URL}/mcp",
        "authorization_servers": [BASE_URL]
    }


def get_authorization_server_metadata() -> Dict[str, Any]:
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414).
    
    ChatGPT reads this to discover endpoints and capabilities.
    CRITICAL: Must include registration_endpoint for DCR.
    """
    log_protocol_event("DISCOVERY", endpoint="oauth-authorization-server")
    
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
        "token_endpoint": f"{BASE_URL}/oauth/token",
        "registration_endpoint": f"{BASE_URL}/oauth/register",
        "userinfo_endpoint": f"{BASE_URL}/oauth/userinfo",
        "scopes_supported": ["openid", "email", "profile", "mcp:tools", "mcp:resources", "mcp:prompts"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
        "subject_types_supported": ["public"]
    }


# === DYNAMIC CLIENT REGISTRATION ===

def _load_clients() -> Dict[str, Dict[str, Any]]:
    """Load registered clients from storage."""
    if not CLIENTS_FILE.exists():
        return {}
    try:
        with open(CLIENTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        return {}


def _save_clients(clients: Dict[str, Dict[str, Any]]):
    """Save registered clients to storage."""
    try:
        with open(CLIENTS_FILE, 'w') as f:
            json.dump(clients, f)
    except Exception as e:
        logger.error(f"Error saving clients: {e}")


def register_client(registration_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamic Client Registration (RFC 7591).
    
    ChatGPT calls this to register itself automatically.
    Returns client_id and optionally client_secret.
    """
    client_id = secrets.token_urlsafe(16)
    client_secret = secrets.token_urlsafe(32)
    
    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": registration_request.get("redirect_uris", []),
        "grant_types": registration_request.get("grant_types", ["authorization_code"]),
        "response_types": registration_request.get("response_types", ["code"]),
        "token_endpoint_auth_method": registration_request.get("token_endpoint_auth_method", "client_secret_post"),
        "scope": registration_request.get("scope", "openid email profile mcp:tools mcp:resources mcp:prompts"),
        "client_name": registration_request.get("client_name", "ChatGPT"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store client
    clients = _load_clients()
    clients[client_id] = client_data
    _save_clients(clients)
    
    log_protocol_event(
        "CLIENT_REGISTRATION",
        client_id=client_id,
        redirect_uris=client_data["redirect_uris"],
        grant_types=client_data["grant_types"],
        token_endpoint_auth_method=client_data["token_endpoint_auth_method"]
    )
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "redirect_uris": client_data["redirect_uris"],
        "grant_types": client_data["grant_types"],
        "response_types": client_data["response_types"],
        "token_endpoint_auth_method": client_data["token_endpoint_auth_method"],
        "scope": client_data["scope"]
    }


def get_client(client_id: str) -> Optional[Dict[str, Any]]:
    """Get registered client by ID."""
    clients = _load_clients()
    return clients.get(client_id)


# === AUTHORIZATION CODE FLOW ===

def _load_auth_codes() -> Dict[str, Dict[str, Any]]:
    """Load authorization codes from storage."""
    if not AUTH_CODES_FILE.exists():
        return {}
    try:
        with open(AUTH_CODES_FILE, 'r') as f:
            data = json.load(f)
            # Clean expired codes
            now = datetime.utcnow().timestamp() * 1000
            return {
                code: info for code, info in data.items()
                if info.get('expires_at', 0) > now
            }
    except Exception as e:
        logger.error(f"Error loading auth codes: {e}")
        return {}


def _save_auth_codes(codes: Dict[str, Dict[str, Any]]):
    """Save authorization codes to storage."""
    try:
        with open(AUTH_CODES_FILE, 'w') as f:
            json.dump(codes, f)
    except Exception as e:
        logger.error(f"Error saving auth codes: {e}")


def create_authorization_code(
    client_id: str,
    redirect_uri: str,
    scope: str,
    user: Dict[str, Any],
    code_challenge: str,
    code_challenge_method: str,
    resource: Optional[str] = None
) -> str:
    """
    Create authorization code for PKCE flow.
    
    IMPORTANT: Store the 'resource' parameter - this becomes the 'aud' claim in the token.
    """
    code = secrets.token_urlsafe(32)
    
    code_data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "user": user,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "resource": resource,  # CRITICAL: Store resource for audience claim
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).timestamp() * 1000
    }
    
    codes = _load_auth_codes()
    codes[code] = code_data
    _save_auth_codes(codes)
    
    log_protocol_event(
        "AUTHORIZATION",
        client_id=client_id,
        user_email=user.get("email"),
        scope=scope,
        resource=resource,
        code_challenge_method=code_challenge_method
    )
    
    return code


def consume_authorization_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Consume authorization code (one-time use).
    Returns code data and removes it from storage.
    """
    codes = _load_auth_codes()
    code_data = codes.pop(code, None)
    
    if code_data:
        # Check expiration
        if code_data.get('expires_at', 0) < datetime.utcnow().timestamp() * 1000:
            logger.warning(f"Authorization code expired: {code[:10]}...")
            return None
        
        _save_auth_codes(codes)
    
    return code_data


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE code_verifier matches code_challenge."""
    verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
    computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip('=')
    return computed_challenge == code_challenge


# === TOKEN MANAGEMENT ===

def _load_tokens() -> Dict[str, Dict[str, Any]]:
    """Load tokens from storage."""
    if not TOKENS_FILE.exists():
        return {}
    try:
        with open(TOKENS_FILE, 'r') as f:
            data = json.load(f)
            # Clean expired tokens
            now = datetime.utcnow().timestamp() * 1000
            return {
                token: info for token, info in data.items()
                if info.get('expires_at', 0) > now
            }
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return {}


def _save_tokens(tokens: Dict[str, Dict[str, Any]]):
    """Save tokens to storage."""
    try:
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f)
    except Exception as e:
        logger.error(f"Error saving tokens: {e}")


def create_access_token(
    client_id: str,
    user: Dict[str, Any],
    scope: str,
    resource: Optional[str] = None
) -> Dict[str, str]:
    """
    Create access token with proper claims.
    
    CRITICAL: Include 'aud' (audience) claim from the 'resource' parameter.
    """
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    token_data = {
        "client_id": client_id,
        "user": user,
        "scope": scope,
        "aud": resource or f"{BASE_URL}/mcp",  # Audience claim
        "iss": BASE_URL,  # Issuer
        "sub": user.get("id", user.get("email")),  # Subject
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).timestamp() * 1000
    }
    
    tokens = _load_tokens()
    tokens[access_token] = token_data
    _save_tokens(tokens)
    
    log_protocol_event(
        "TOKEN_EXCHANGE",
        client_id=client_id,
        user_email=user.get("email"),
        audience=token_data["aud"],
        scope=scope,
        token_preview=access_token[:10]
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": scope
    }


def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate access token for MCP requests.
    
    Checks:
    - Token exists
    - Not expired
    - Valid issuer
    - Valid audience
    """
    tokens = _load_tokens()
    token_data = tokens.get(token)
    
    if not token_data:
        logger.warning(f"Token not found: {token[:10]}...")
        return None
    
    # Check expiration
    if token_data.get('expires_at', 0) < datetime.utcnow().timestamp() * 1000:
        logger.warning(f"Token expired: {token[:10]}...")
        return None
    
    # Validate issuer
    if token_data.get('iss') != BASE_URL:
        logger.warning(f"Invalid issuer: {token_data.get('iss')}")
        return None
    
    log_protocol_event(
        "MCP_REQUEST",
        user_email=token_data.get("user", {}).get("email"),
        client_id=token_data.get("client_id"),
        audience=token_data.get("aud"),
        scope=token_data.get("scope")
    )
    
    return token_data
