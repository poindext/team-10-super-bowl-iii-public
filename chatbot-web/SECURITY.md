# Security Architecture

This document explains the security architecture of the chatbot web application and confirms that all credentials and API endpoints are properly protected.

## Security Model: Client-Server Separation

### ✅ **Frontend (Client-Side) - Public**
The frontend (`frontend/`) contains **NO sensitive information**:
- ❌ No API keys or credentials
- ❌ No IRIS endpoint URLs
- ❌ No OpenAI API keys
- ✅ Only calls `/chat` endpoint (relative path)
- ✅ All code is viewable by end users (as intended)

**What the frontend can see:**
- Only the `/chat` endpoint path (which is your own backend)
- User messages and bot responses
- No access to external APIs

### ✅ **Backend (Server-Side) - Protected**
The backend (`backend/`) contains **ALL sensitive information**:
- ✅ OpenAI API key (from `OPENAI_API_KEY` environment variable)
- ✅ IRIS endpoint URL (from `IRIS_ENDPOINT` environment variable)
- ✅ IRIS authentication credentials (from environment variables)
- ✅ All external API calls happen server-side only

**What the backend does:**
1. Receives user messages from frontend
2. Calls OpenAI API with credentials (server-side only)
3. Executes tool calls (calls IRIS endpoint with credentials)
4. Returns only the final response text to frontend

## Security Guarantees

### 🔒 **Credentials Protection**
- **OpenAI API Key**: Stored in `OPENAI_API_KEY` environment variable, never in code
- **IRIS Credentials**: Stored in environment variables (`IRIS_USERNAME`, `IRIS_PASSWORD`, `IRIS_BEARER_TOKEN`, or `IRIS_API_KEY`)
- **IRIS Endpoint**: Stored in `IRIS_ENDPOINT` environment variable
- **No credentials in frontend code**: Impossible for users to discover

### 🔒 **API Endpoint Protection**
- IRIS endpoint URL is only in backend code/environment variables
- Frontend never knows the IRIS endpoint exists
- All API calls are proxied through your backend

### 🔒 **Network Security**
- Frontend only communicates with your backend (`/chat`)
- Backend makes all external API calls
- Users cannot directly call OpenAI or IRIS APIs

## Deployment Security Checklist

When deploying to IIS/EC2:

1. ✅ **Environment Variables**: Set all credentials as environment variables on the server
   ```powershell
   setx OPENAI_API_KEY "sk-..."
   setx IRIS_ENDPOINT "http://..."
   setx IRIS_USERNAME "your_user"
   setx IRIS_PASSWORD "your_pass"
   ```

2. ✅ **CORS Configuration**: Set `ALLOWED_ORIGINS` to your domain in production
   ```powershell
   setx ALLOWED_ORIGINS "https://yourdomain.com"
   ```

3. ✅ **HTTPS**: Use HTTPS for all frontend-backend communication

4. ✅ **Backend Access**: Ensure backend (port 8000) is only accessible from localhost/IIS, not publicly exposed

5. ✅ **File Permissions**: Ensure `.env` files (if used) are not in web-accessible directories

## What Users CANNOT Access

Even if users inspect the frontend code, they **cannot**:
- ❌ See your OpenAI API key
- ❌ See your IRIS endpoint URL
- ❌ See your IRIS credentials
- ❌ Directly call OpenAI API
- ❌ Directly call IRIS API
- ❌ Access any backend environment variables

## What Users CAN Access

Users can see (and this is safe):
- ✅ Frontend HTML/CSS/JavaScript code
- ✅ The `/chat` endpoint path (which is your own backend)
- ✅ Their own messages and bot responses
- ✅ Network requests to `/chat` (but not the credentials used)

## Verification

To verify security:

1. **Inspect Frontend Code**: Open browser DevTools → Sources → Check `app.js`
   - You'll see only `/chat` endpoint, no credentials

2. **Inspect Network Traffic**: Open DevTools → Network → Check requests
   - You'll see requests to `/chat` only
   - No requests to OpenAI or IRIS endpoints

3. **Check Backend Code**: Review `backend/app.py`
   - All credentials come from `os.getenv()` (environment variables)
   - No hardcoded credentials

## Summary

✅ **All credentials are server-side only**  
✅ **All API endpoints are server-side only**  
✅ **Frontend has zero access to sensitive data**  
✅ **Users cannot discover or access credentials**  
✅ **Architecture provides clear client-server separation**

This architecture follows security best practices for web applications.

