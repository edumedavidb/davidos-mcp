# DavidOS MCP Server - Lessons Learned

## ChatGPT OAuth Integration Debugging Session
**Date:** March 14, 2026

---

## Issue 1: Client ID Not Auto-Populating in ChatGPT Connector

**Hypothesis:**
ChatGPT requires CIMD (Client ID Metadata Document) support advertised in OAuth discovery endpoints to auto-populate client credentials.

**Actions Taken:**
- Added `client_id` field to `/.well-known/oauth-authorization-server` metadata
- Added `client_id` field to `/.well-known/openid-configuration` metadata
- Added `client_id_metadata_document_supported: true` to OAuth metadata

**Result:**
✅ **RESOLVED** - Client ID auto-population improved but not fully reliable in ChatGPT UI.

---

## Issue 2: Internal Server Error on `/oauth/authorize`

**Hypothesis:**
Missing import for `RedirectResponse` causing runtime error when redirecting to Google OAuth.

**Actions Taken:**
- Added `from fastapi.responses import RedirectResponse` import
- Deployed fix to Railway

**Result:**
✅ **RESOLVED** - OAuth authorize endpoint now redirects successfully to Google login.

---

## Issue 3: ChatGPT Backend 400 Error on OAuth Callback

**Hypothesis:**
OAuth token endpoint not parsing form data correctly - ChatGPT sends `application/x-www-form-urlencoded` but endpoint expected query parameters.

**Actions Taken:**
- Modified `/oauth/token` endpoint to parse form data instead of query params
- Added fallback to query params if form parsing fails
- Added detailed logging for debugging

**Result:**
✅ **RESOLVED** - Token endpoint now correctly parses ChatGPT's requests.

---

## Issue 4: Tools Not Appearing in ChatGPT (401 Unauthorized on MCP Calls)

**Hypothesis:**
In-memory token storage (`_access_tokens` dictionary) is lost when Railway restarts the server between OAuth token creation and MCP endpoint calls.

**Actions Taken:**
1. Added session-based authentication as backup
2. Configured session cookies with `SameSite=None` and `Secure=True` for cross-site requests
3. Implemented persistent file-based token storage in `/tmp/oauth_tokens.json`
4. Created `token_storage.py` module for managing persistent tokens

**Result:**
🔄 **IN PROGRESS** - Persistent token storage implemented, awaiting verification.

---

## Issue 5: MCP Endpoint Path Mismatch

**Hypothesis:**
Working ChatGPT MCP examples use `POST /` (root path) instead of `POST /mcp` as the MCP endpoint.

**Actions Taken:**
- Added MCP endpoint at root path `POST /`
- Kept legacy `POST /mcp` endpoint for backward compatibility
- Both endpoints now call shared `handle_mcp_request()` function

**Result:**
🔄 **IN PROGRESS** - Root path endpoint added, awaiting ChatGPT connector test.

---

## Issue 6: NameError in OAuth Token Endpoint (500 Error)

**Hypothesis:**
Debug logging line referencing deleted `_auth_codes` variable causing crash during token exchange.

**Actions Taken:**
- Removed line: `logger.info(f"Available auth codes: {list(_auth_codes.keys())[:3]}...")`
- Fixed logging to only reference existing variables
- Deployed fix to Railway

**Result:**
🔄 **IN PROGRESS** - Bug fixed, awaiting OAuth flow retry.

---

## Key Technical Insights

### 1. ChatGPT OAuth Client Behavior
- Sends token requests as `application/x-www-form-urlencoded` form data
- Requires proper CORS headers with `credentials: true`
- May not reliably preserve session cookies between requests
- Expects MCP endpoint at root path `/` by default

### 2. Railway Deployment Constraints
- In-memory storage is unreliable due to server restarts
- `/tmp` directory persists across requests but may be cleared periodically
- Need persistent storage (file-based, Redis, or database) for production

### 3. MCP Protocol Requirements
- OAuth 2.1 with PKCE required for ChatGPT integration
- Discovery endpoints must be at `/.well-known/` paths
- Bearer token authentication on all MCP requests
- Tools must be returned in specific JSON-RPC format

### 4. Session vs Token Authentication
- Session cookies don't reliably work with ChatGPT's HTTP client
- Bearer tokens are more reliable but require persistent storage
- Hybrid approach (both session and token) provides best compatibility

---

## Pending Verification

### Test 1: OAuth Flow Completion
- [ ] ChatGPT successfully completes OAuth flow
- [ ] Token exchange returns 200 (not 500)
- [ ] Access token stored in `/tmp/oauth_tokens.json`

### Test 2: Tool Discovery
- [ ] ChatGPT calls MCP endpoint with Bearer token
- [ ] Server validates token from persistent storage
- [ ] All 7 tools returned in `list_tools` response
- [ ] Tools appear in ChatGPT connector interface

### Test 3: Tool Execution
- [ ] User can invoke tools from ChatGPT conversation
- [ ] Tool responses include proper content and metadata
- [ ] Widget URIs are recognized by ChatGPT

---

## Next Steps

1. **Immediate:** Verify OAuth flow works with latest fixes
2. **Short-term:** Consider Redis or database for token storage if `/tmp` proves unreliable
3. **Long-term:** Implement token refresh flow for long-lived sessions
4. **Alternative:** Explore Custom GPT with Actions as simpler integration path

---

## References

- [OpenAI Apps SDK Authentication](https://developers.openai.com/apps-sdk/build/auth/)
- [MCP Authorization Spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
- [Working MCP OAuth Example (Supabase)](https://gist.github.com/ruvnet/7b6843c457822cbcf42fc4aa635eadbb)
- [ChatGPT MCP OAuth Issues Thread](https://community.openai.com/t/chatgpt-does-not-re-trigger-oauth-on-401-www-authenticate-for-mcp-tool-calls/1374168)
