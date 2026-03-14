# ChatGPT App Submission Guide

## Current Status

✅ **MCP Server Implementation Complete**

The DavidOS MCP server is fully implemented and deployed with:

- **7 MCP Tools**: get_context, read_file, search_memory, append_decision, append_question, append_weekly_note, update_section
- **5 Widget Resources**: Versioned UI components for rendering tool outputs
- **Google OAuth Authentication**: Secure access control with domain verification
- **Full MCP Protocol Support**: list_tools, call_tool, list_resources, read_resource
- **Compatibility Features**: Dual metadata format, read-only annotations, response validation, comprehensive logging

**Deployed at**: https://davidos-mcp-production.up.railway.app

---

## MCP Server Endpoints

### Protocol Endpoint
- **POST /mcp** - Main MCP protocol endpoint (requires authentication)
  - Supports: `list_tools`, `call_tool`, `list_resources`, `read_resource`, `list_prompts`, `get_prompt`

### Authentication Endpoints
- **GET /login** - Initiate Google OAuth flow
- **GET /auth/google/callback** - OAuth callback handler
- **GET /me** - Get current user info
- **GET /logout** - End session

### Utility Endpoints
- **GET /health** - Health check
- **GET /** - Homepage with auth status
- **GET /test** - MCP protocol test page

---

## Testing the MCP Server

### 1. Test Page (Easiest)
Visit: https://davidos-mcp-production.up.railway.app/test

This provides a browser-based interface to test all MCP methods:
- List available tools
- Execute tools with parameters
- View widget resources
- Test authentication

### 2. Manual API Testing

**Authenticate first:**
```bash
# Visit in browser to get session cookie
open https://davidos-mcp-production.up.railway.app/login
```

**Test list_tools:**
```bash
curl -X POST https://davidos-mcp-production.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"method": "list_tools", "params": {}}'
```

**Test call_tool:**
```bash
curl -X POST https://davidos-mcp-production.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "method": "call_tool",
    "params": {
      "name": "get_context",
      "arguments": {}
    }
  }'
```

---

## ChatGPT Apps SDK Integration

### Current Implementation Status

✅ **MCP Protocol Compliant**
- JSON-RPC style method routing
- Proper tool descriptors with input schemas
- Widget resources with `text/html;profile=mcp-app` MIME type
- Dual metadata format (MCP standard + OpenAI alias)

✅ **Tool Metadata**
```json
{
  "name": "get_context",
  "description": "Retrieve the strategic context from context.md",
  "inputSchema": {...},
  "annotations": {
    "readOnlyHint": true
  },
  "_meta": {
    "ui": {
      "resourceUri": "ui://widget/context/v1"
    },
    "openai/outputTemplate": "ui://widget/context/v1"
  }
}
```

✅ **Widget Resources**
- Versioned URIs (v1)
- Safe async rendering pattern
- Proper MIME type
- Reads from `window.openai.toolOutput.structuredContent`

✅ **Response Validation**
- All tool responses validated for required fields
- Comprehensive error logging
- Execution time tracking

---

## Next Steps for ChatGPT App Submission

### Option 1: Direct MCP Server (Current Approach)

**Status**: The Python MCP server is ready but may need additional work for ChatGPT Apps SDK compatibility.

**Considerations**:
- Python MCP SDK has limited remote server support
- ChatGPT Apps SDK documentation primarily shows TypeScript examples
- May require SSE (Server-Sent Events) transport instead of HTTP POST

**Action Required**:
1. Research if ChatGPT Apps SDK accepts HTTP POST MCP servers
2. If SSE required, implement SSE transport layer
3. Test with ChatGPT Apps SDK runtime

### Option 2: TypeScript MCP Wrapper (Recommended by OpenAI)

**Why**: OpenAI's Apps SDK documentation and examples use TypeScript with `@modelcontextprotocol/sdk`

**Architecture**:
```
ChatGPT Apps SDK
    ↓
TypeScript MCP Server (SSE transport)
    ↓ (HTTP calls)
Python FastAPI Server (existing)
    ↓
DavidOS files
```

**Benefits**:
- Full ChatGPT Apps SDK compatibility
- Official SDK support
- Keep existing Python implementation
- Clean separation of concerns

**Implementation**:
1. Create TypeScript MCP server using `@modelcontextprotocol/sdk`
2. Implement SSE transport
3. Proxy tool calls to Python API
4. Register widgets from Python server
5. Deploy TypeScript server to Railway

### Option 3: Custom GPT with Actions (Alternative)

**Why**: Simpler integration path if full MCP server proves complex

**How**:
1. Create Custom GPT in ChatGPT
2. Import OpenAPI spec (already created at `davidos-mcp/openapi.yaml`)
3. Configure OAuth with Google credentials
4. ChatGPT calls HTTP endpoints directly

**Limitations**:
- Not a "ChatGPT App" in the Apps SDK sense
- No widget rendering
- Limited to OpenAPI/REST paradigm

---

## Required for Submission

### 1. App Manifest
Location: `davidos-mcp/app-manifest.json`

Current manifest includes:
- App metadata (name, description, version)
- MCP server URL
- OAuth configuration
- Capabilities declaration

**May need updates** depending on final submission format.

### 2. Privacy Policy & Terms of Service

**Status**: Not yet created

**Required URLs**:
- `/privacy` - Privacy policy
- `/terms` - Terms of service

**Action**: Create simple privacy/terms pages or host externally.

### 3. OAuth Configuration

**Current Setup**:
- Google OAuth with domain restriction
- Client ID: `496166341299-046np9lo98e1eajj90582mejdvu7p77l.apps.googleusercontent.com`
- Allowed domain: `edume.com`
- Redirect URI: `https://davidos-mcp-production.up.railway.app/auth/google/callback`

**For Public Submission**: May need to remove domain restriction or create separate OAuth client.

### 4. Documentation

**Needed**:
- User guide for DavidOS tools
- Example use cases
- Setup instructions
- API documentation

---

## Recommended Next Steps

### Immediate (Before Submission)

1. **Verify MCP Protocol Compatibility**
   - Test with ChatGPT Apps SDK if available
   - Confirm HTTP POST vs SSE transport requirements
   - Validate tool and resource discovery

2. **Add Privacy & Terms Pages**
   - Create `/privacy` endpoint
   - Create `/terms` endpoint
   - Update app manifest URLs

3. **Test All Tools End-to-End**
   - Verify all 7 tools execute correctly
   - Test widget rendering
   - Confirm write operations persist
   - Check error handling

4. **Create User Documentation**
   - Tool descriptions and examples
   - Setup guide
   - Use case scenarios

### If TypeScript Wrapper Needed

1. **Create TypeScript MCP Server**
   ```bash
   npm install @modelcontextprotocol/sdk
   npm install @modelcontextprotocol/ext-apps
   ```

2. **Implement SSE Transport**
   - Follow OpenAI Apps SDK examples
   - Proxy to Python API

3. **Deploy to Railway**
   - Separate service or same container
   - Configure environment variables

### For Submission

1. **Submit to OpenAI**
   - Follow ChatGPT Apps submission guidelines
   - Provide app manifest
   - Include documentation
   - Wait for review

2. **Monitor Deployment**
   - Watch Railway logs
   - Track authentication flows
   - Monitor tool execution

---

## Current Architecture

```
User
  ↓
ChatGPT
  ↓
[Apps SDK Runtime] ← (This is where integration happens)
  ↓
DavidOS MCP Server (Python/FastAPI)
  ├─ /mcp endpoint (MCP protocol)
  ├─ Tools (7 operations)
  ├─ Widgets (5 UI components)
  └─ OAuth (Google authentication)
  ↓
DavidOS Files (markdown)
```

**Deployed**: https://davidos-mcp-production.up.railway.app

**Status**: MCP server ready, awaiting Apps SDK integration testing

---

## Support & Debugging

**Test Page**: https://davidos-mcp-production.up.railway.app/test

**Logs**: Railway dashboard → davidos-mcp-production → Deployments → Logs

**Repository**: https://github.com/edumedavidb/davidos-mcp

**Issues**: Track in GitHub Issues or Railway deployment logs
