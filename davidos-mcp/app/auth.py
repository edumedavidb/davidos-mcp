"""Google OAuth authentication for DavidOS MCP Server."""

import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer

from .config import settings

logger = logging.getLogger("davidos-mcp")

# OAuth configuration
oauth = OAuth()

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name='google',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar.events',
            'access_type': 'offline',
            'prompt': 'consent'
        }
    )


def get_current_user(request: Request) -> dict:
    """Get the current authenticated user from session.
    
    Raises:
        HTTPException: If user is not authenticated or domain not allowed.
    """
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify domain if configured
    if settings.google_allowed_domain:
        email = user.get('email', '')
        if not email.endswith(f"@{settings.google_allowed_domain}"):
            raise HTTPException(
                status_code=403, 
                detail=f"Email domain not allowed. Must be @{settings.google_allowed_domain}"
            )
    
    return user


async def login(request: Request):
    """Initiate Google OAuth login flow."""
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="OAuth not configured")
    
    # Build redirect URI
    redirect_uri = str(request.url_for('auth_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def auth_callback(request: Request):
    """Handle OAuth callback from Google."""
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="OAuth not configured")
    
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")
    
    # Get user info
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    email = user_info.get('email')
    
    # Verify domain
    if settings.google_allowed_domain:
        if not email or not email.endswith(f"@{settings.google_allowed_domain}"):
            raise HTTPException(
                status_code=403,
                detail=f"Email domain not allowed. Must be @{settings.google_allowed_domain}"
            )
    
    # Store user session
    request.session['user'] = {
        'email': email,
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
        'access_token': token.get('access_token'),
        'refresh_token': token.get('refresh_token')
    }
    
    logger.info(f"User authenticated: {email}")
    
    # Redirect to home or dashboard
    return RedirectResponse(url='/')


async def get_me(request: Request, user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        'email': user.get('email'),
        'name': user.get('name'),
        'picture': user.get('picture')
    }


async def logout(request: Request):
    """Clear user session."""
    request.session.clear()
    return {"status": "logged out"}
