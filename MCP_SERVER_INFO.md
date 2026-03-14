# DavidOS MCP Server Information

## Server URL
**Production**: https://davidos-mcp-production.up.railway.app

## MCP Endpoint
**POST**: https://davidos-mcp-production.up.railway.app/mcp

## OAuth Credentials for ChatGPT
- **Client ID**: `davidos-mcp-chatgpt-client`
- **Client Secret**: `davidos-mcp-secret-2026-change-in-production`

## Key Endpoints

### Authentication
- **Login**: https://davidos-mcp-production.up.railway.app/login
- **Callback**: https://davidos-mcp-production.up.railway.app/auth/google/callback
- **User Info**: https://davidos-mcp-production.up.railway.app/me
- **Logout**: https://davidos-mcp-production.up.railway.app/logout

### OAuth 2.1 + OIDC
- **OAuth Authorize**: https://davidos-mcp-production.up.railway.app/oauth/authorize
- **OAuth Token**: https://davidos-mcp-production.up.railway.app/oauth/token
- **OIDC UserInfo**: https://davidos-mcp-production.up.railway.app/oauth/userinfo
- **Protected Resource Metadata**: https://davidos-mcp-production.up.railway.app/.well-known/oauth-protected-resource
- **OAuth Server Metadata**: https://davidos-mcp-production.up.railway.app/.well-known/oauth-authorization-server
- **OIDC Configuration**: https://davidos-mcp-production.up.railway.app/.well-known/openid-configuration

### Utility
- **Health Check**: https://davidos-mcp-production.up.railway.app/health
- **Test Page**: https://davidos-mcp-production.up.railway.app/test
- **Privacy Policy**: https://davidos-mcp-production.up.railway.app/privacy
- **Terms of Service**: https://davidos-mcp-production.up.railway.app/terms

## MCP Tools (7 total)
1. **get_context** - Retrieve strategic context from context.md (read-only)
2. **read_file** - Read any DavidOS file by path (read-only)
3. **search_memory** - Search across all DavidOS content (read-only)
4. **append_decision** - Record a strategic decision
5. **append_question** - Add an open strategic question
6. **append_weekly_note** - Add a note to weekly review
7. **update_section** - Update a specific section in a markdown file

## Widget Resources (5 total)
- `ui://widget/decision/v1` - Decision summaries
- `ui://widget/context/v1` - Strategic context display
- `ui://widget/question/v1` - Open questions
- `ui://widget/search/v1` - Search results
- `ui://widget/file/v1` - File content viewer

## Deployment
- **Platform**: Railway
- **Repository**: https://github.com/edumedavidb/davidos-mcp
- **Logs**: Railway Dashboard → davidos-mcp-production → Deployments → Logs

## ChatGPT Connector Setup

### OAuth Configuration
```
Client ID: davidos-mcp-chatgpt-client
Client Secret: davidos-mcp-secret-2026-change-in-production
Token endpoint auth method: client_secret_post

Default scopes:
openid
email
profile
mcp:tools
mcp:resources
mcp:prompts
```

### Connector Details
```
Name: DavidOS Strategic Context
Description: Access and manage strategic product context, decisions, and open questions from DavidOS
Connector URL: https://davidos-mcp-production.up.railway.app/mcp
```

## Quick Access Commands

### Test MCP Protocol
```bash
# List tools
curl -X POST https://davidos-mcp-production.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "list_tools", "params": {}}'

# List resources
curl -X POST https://davidos-mcp-production.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "list_resources", "params": {}}'
```

### Browser Test
Open: https://davidos-mcp-production.up.railway.app/test

## Environment Variables (Railway)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_ALLOWED_DOMAIN` (edume.com)
- `SESSION_SECRET`
- `PORT` (auto-assigned by Railway)

## Support
- **Issues**: https://github.com/edumedavidb/davidos-mcp/issues
- **Documentation**: See CHATGPT_APP_SUBMISSION.md
- **Contact**: david.barnes@edume.com
