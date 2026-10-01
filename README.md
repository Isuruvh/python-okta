# Python Okta - PKCE Authorization Code Flow

A production-ready Python Flask web application demonstrating **Okta Sign-In Widget deployment** with **PKCE (Proof Key for Code Exchange)** authorization code flow for secure OAuth 2.0 authentication in traditional backend web applications.

## Overview

This project implements the OAuth 2.0 Authorization Code Flow with PKCE, the recommended authentication method for server-side web applications. It integrates Okta's identity platform to provide secure user authentication, session management, and single sign-on (SSO) capabilities.

### Key Features

✅ **PKCE-Enhanced Authorization Code Flow** - Industry-standard, secure OAuth 2.0 implementation  
✅ **Okta Integration** - Full Okta identity provider support  
✅ **Flask-based Backend** - Lightweight, scalable Python web framework  
✅ **Session Management** - Secure user session handling with Flask-Login  
✅ **User Profile** - Display authenticated user information  
✅ **Single Sign-Out** - Secure logout with Okta session termination  
✅ **CORS Support** - Cross-origin resource sharing enabled  
✅ **Environment Configuration** - Secure credential management via .env file  

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Architecture

### Authentication Flow

```
┌─────────────┐                 ┌──────────────┐                 ┌─────────────┐
│   Browser   │                 │   Flask App  │                 │    Okta     │
│   (Client)  │                 │   (Backend)  │                 │   (IdP)     │
└─────────────┘                 └──────────────┘                 └─────────────┘
      │                               │                               │
      │────── GET /signin ──────────► │                               │
      │                               │ Generate PKCE Challenge       │
      │                               │ (code_verifier + code_challenge)
      │                               │ Generate state parameter      │
      │                               │                               │
      │ ◄───── Redirect (auth_uri) ── │ ◄─────── /oauth2/v1/authorize
      │                               │          (with PKCE params)
      │                               │                               │
      │─────── User Login/Consent ──► │ ◄───────── Okta Login Page ───
      │                               │                               │
      │ ◄───────────────────────────────────────────────────────────────
      │      Redirect callback        │
      │      (code + state)           │
      │                               │
      │───── GET /callback ─────────► │
      │      (code + state)           │
      │                               │ Validate state
      │                               │ Exchange code for token
      │                               │ (using code_verifier)
      │                               │
      │                               │──────► POST /oauth2/v1/token
      │                               │        (code + code_verifier)
      │                               │                               │
      │                               │◄────── Access Token + ID Token
      │                               │        (JWT format)
      │                               │
      │                               │ Get user info
      │                               │──────► GET /oauth2/v1/userinfo
      │                               │        (Bearer access_token)
      │                               │                               │
      │                               │◄────── User Claims (email, name, etc.)
      │                               │
      │                               │ Create session & login user
      │ ◄─── Set Session Cookie ──── │
      │                               │
      │◄────── Redirect /profile ──── │
      │
      │───── GET /profile ──────────► │ (with session cookie)
      │                               │
      │ ◄───── HTML Profile Page ──── │
      │
```

### PKCE Mechanism

The PKCE extension protects against authorization code interception attacks by:

1. **Code Verifier**: A cryptographically random string (43-128 characters) generated on the backend
2. **Code Challenge**: A base64url-encoded SHA-256 hash of the code verifier
3. **Authorization Request**: Client sends code_challenge to authorization server
4. **Token Exchange**: Client proves possession of code_verifier when exchanging the authorization code

This makes it impossible for attackers to use a stolen authorization code without the original code_verifier.

---

## Prerequisites

### System Requirements
- Python 3.8 or higher
- pip package manager
- A modern web browser (Chrome, Firefox, Safari, Edge)

### Okta Account
- An active Okta developer account ([Free tier available](https://developer.okta.com/signup))
- Access to Okta Admin Console
- An Okta organization (domain) created

### Required Information from Okta
You'll need these values from your Okta application configuration:
- **OKTA_ISSUER**: Your Okta authorization server issuer (e.g., `https://dev-123456.okta.com/oauth2/default`)
- **OKTA_CLIENT_ID**: OAuth 2.0 client ID
- **OKTA_CLIENT_SECRET**: OAuth 2.0 client secret
- **OKTA_AUTH_URI**: Authorization endpoint (e.g., `https://dev-123456.okta.com/oauth2/default/v1/authorize`)
- **OKTA_TOKEN_URI**: Token endpoint (e.g., `https://dev-123456.okta.com/oauth2/default/v1/token`)
- **OKTA_USERINFO_URI**: UserInfo endpoint (e.g., `https://dev-123456.okta.com/oauth2/default/v1/userinfo`)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Isuruvh/python-okta.git
cd python-okta
```

### Step 2: Create a Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Required Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `Flask 3.1.2` - Web framework
- `Flask-Login 0.6.3` - User session management
- `Flask-CORS` - CORS support
- `requests` - HTTP client library
- `python-dotenv` - Environment variable management
- `Werkzeug 3.1.3` - Flask's WSGI utility library

### Step 4: Create `.env` Configuration File

Create a `.env` file in the project root with your Okta credentials:

```bash
# Okta Configuration
OKTA_ISSUER=https://dev-123456.okta.com/oauth2/default
OKTA_CLIENT_ID=0oaXXXXXXXXXXXXXXXXX
OKTA_CLIENT_SECRET=your_client_secret_here
OKTA_AUTH_URI=https://dev-123456.okta.com/oauth2/default/v1/authorize
OKTA_TOKEN_URI=https://dev-123456.okta.com/oauth2/default/v1/token
OKTA_USERINFO_URI=https://dev-123456.okta.com/oauth2/default/v1/userinfo
OKTA_REDIRECT_URI=http://localhost:5000/callback
```

> ⚠️ **Security Warning**: Never commit `.env` to version control. It's already listed in `.gitignore`.

---

## Configuration

### Okta Application Setup

#### 1. Create an OAuth 2.0 Application in Okta

1. Sign in to your Okta Admin Console
2. Navigate to **Applications** → **Applications**
3. Click **Create App Integration**
4. Select **OIDC - OpenID Connect** and **Web Application**
5. Click **Next**

#### 2. Configure Application Settings

- **App integration name**: Python Okta PKCE Demo
- **Grant type**: Authorization Code, Refresh Token
- **Sign-in redirect URI**: `http://localhost:5000/callback`
- **Sign-out redirect URI**: `http://localhost:5000/`
- **Scopes**: `openid`, `profile`, `offline_access`

Enable the **Refresh Token** grant and allow the `offline_access` scope in Okta. The app displays whether Okta returned a refresh token; the token itself is kept server-side and is never rendered in the profile.

#### 3. Obtain Credentials

After creating the application:
1. Copy the **Client ID** and **Client Secret** from the application settings
2. Your **Issuer** is displayed in the top-right corner of the Admin Console or found in **API** → **Authorization Servers**

#### 4. Add User Claims (Optional)

To include additional user information in ID tokens:
1. Go to **API** → **Authorization Servers** → **default**
2. Click the **Claims** tab
3. Verify these standard OIDC claims exist: `email`, `given_name`, `family_name`

---

## Project Structure

```
python-okta/
├── app.py                    # Main Flask application & OAuth logic
├── user.py                   # User model & in-memory database
├── .env.example              # Example environment configuration
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── templates/
    ├── signin.html           # Sign-in landing page
    └── profile.html          # User profile display page
```

### File Descriptions

#### `app.py`
Main application file containing:
- Flask app initialization
- OAuth 2.0 flow implementation
- Endpoint handlers:
  - `/` - Home/landing page
  - `/signin` - Initiates PKCE flow
    - `/callback` - OAuth callback handler used by the local Okta configuration
    - `/authorization-code/callback` - Compatibility callback route
  - `/profile` - Protected user profile page
  - `/signout` - Logout handler

#### `user.py`
User management:
- `User` class extending Flask-Login's `UserMixin`
- In-memory user database (`USERS_DB`)
- User creation and retrieval methods

#### `templates/signin.html`
Landing page with:
- Sign-in button
- Brief application description
- OAuth 2.0 flow initiation

#### `templates/profile.html`
Protected page displaying:
- Authenticated user information
- User claims (email, name)
- Sign-out option

---

## How It Works

### 1. **User Initiates Sign-In**

User clicks "Sign In" button on homepage, which triggers `GET /signin`

```python
@app.route("/signin")
def signin():
    # Generate random state to prevent CSRF attacks
    session['app_state'] = secrets.token_urlsafe(64)
    
    # Generate PKCE code verifier
    session['code_verifier'] = secrets.token_urlsafe(64)
    
    # Create code challenge from verifier
    hashed = hashlib.sha256(session['code_verifier'].encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii').strip('=')
    
    # Prepare authorization request parameters
    query_params = {
        'client_id': config["client_id"],
        'redirect_uri': config["redirect_uri"],
        'scope': "openid profile offline_access",
        'state': session['app_state'],
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',  # SHA-256
        'response_type': 'code',
        'response_mode': 'query'
    }
    
    # Redirect to Okta authorization endpoint
    return redirect(auth_uri + "?" + urlencode(query_params))
```

**Key Points:**
- `code_verifier`: Securely stored in Flask session (server-side)
- `code_challenge`: Sent to Okta (derived from verifier)
- `state`: Prevents CSRF attacks by validating on callback
- `S256`: SHA-256 based PKCE (most secure method)

---

### 2. **User Authenticates with Okta**

- User is redirected to Okta's login page
- User enters credentials (username + password or MFA)
- Okta validates identity and displays consent screen
- User grants application access to requested scopes

---

### 3. **Okta Issues Authorization Code**

After successful authentication, Okta redirects user back to:

```
http://localhost:5000/callback?code=XXXXXXX&state=YYYYYYY
```

---

### 4. **Backend Exchanges Code for Tokens**

The callback handler processes the authorization code:

```python
@app.route("/callback")
@app.route("/authorization-code/callback")
def callback():
    # 1. Validate state parameter
    app_state = request.args.get("state")
  if not session.get('app_state') or app_state != session['app_state']:
        return "The app state doesn't match", 403
    
    # 2. Extract authorization code
    code = request.args.get("code")
    if not code:
        return "The code wasn't returned", 403
    
    # 3. Exchange code for tokens using PKCE
    query_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': request.base_url,
        'code_verifier': session['code_verifier'],  # Proves code verifier possession
    }
    
    exchange = requests.post(
        config["token_uri"],
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data=urlencode(query_params),
        auth=(config["client_id"], config["client_secret"]),
    ).json()
    
    # 4. Extract tokens
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]
    session["id_token"] = id_token  # Save for logout
    
    # 5. Get user information
    userinfo = requests.get(
        config["userinfo_uri"],
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()
    
    # 6. Create/load user and establish session
    user = User(
        id_=userinfo["sub"],
        name=userinfo["given_name"],
        email=userinfo["email"]
    )
    login_user(user)
    
    return redirect(url_for("profile"))
```

**Security Features:**
- State validation prevents CSRF
- Code verifier sent server-to-server (never exposed to browser)
- Access token never exposed to frontend
- ID token securely stored in session

---

### 5. **Access Protected Resources**

User is now authenticated and can access protected endpoints:

```python
@app.route("/profile")
@login_required  # Requires active session
def profile():
    return render_template("profile.html", user=current_user)
```

Flask-Login automatically:
- Validates session cookie
- Deserializes user from session
- Rejects unauthorized requests

---

### 6. **User Signs Out**

```python
@app.route("/signout", methods=["GET", "POST"])
@login_required
def signout():
    # 1. Get stored ID token
    id_token = session.get("id_token")
    
    # 2. Clear Flask-Login
    logout_user()
    
    # 3. Clear session cookies
    session.clear()
    
    # 4. Redirect to Okta logout endpoint
    logout_base = f"{config['issuer']}/v1/logout"
    logout_uri = f"{logout_base}?id_token_hint={id_token}&post_logout_redirect_uri={home_url}"
    
    return redirect(logout_uri)
```

**Result:**
- Local session destroyed
- Okta session terminated
- User logged out globally across all connected apps (SSO)

---

## Usage

### Running the Application

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Start Flask development server
python app.py
```

**Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://localhost:5000
```

### Accessing the Application

1. **Open browser**: Navigate to `http://localhost:5000`
2. **Click Sign In**: Initiates PKCE OAuth flow
3. **Authenticate with Okta**: Enter your Okta credentials
4. **Grant Consent**: Approve application access (first time only)
5. **View Profile**: See authenticated user information
6. **Sign Out**: Logs out from application and Okta

---

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page with sign-in button |
| GET | `/signin` | Initiates OAuth 2.0 PKCE flow |
| GET | `/callback` | OAuth callback handler |
| GET | `/authorization-code/callback` | Compatibility callback route |

### Protected Endpoints (Requires Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Display authenticated user profile |
| GET/POST | `/signout` | Sign out and clear sessions |

### Request/Response Examples

#### 1. Authorization Request
```
GET /oauth2/default/v1/authorize?
  client_id=0oaXXXXXXXXXXXXXXXXX&
    redirect_uri=http://localhost:5000/callback&
  response_type=code&
  scope=openid%20profile%20offline_access&
  state=RANDOM_STATE_VALUE&
  code_challenge=CODE_CHALLENGE_SHA256&
  code_challenge_method=S256
```

#### 2. Token Exchange Request
```
POST /oauth2/default/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
redirect_uri=http://localhost:5000/callback&
code_verifier=CODE_VERIFIER_VALUE&
client_id=0oaXXXXXXXXXXXXXXXXX&
client_secret=SECRET_VALUE
```

#### 3. Token Exchange Response
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid profile offline_access",
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZC...",
  "refresh_token": "REDACTED_REFRESH_TOKEN"
}
```

#### 4. UserInfo Request
```
GET /oauth2/default/v1/userinfo
Authorization: Bearer ACCESS_TOKEN
```

#### 5. UserInfo Response
```json
{
  "sub": "00uXXXXXXXXXXXXXXXXX",
  "email": "user@example.com",
  "given_name": "John",
  "family_name": "Doe",
  "email_verified": true
}
```

---

## Security Considerations

### 1. **PKCE (Proof Key for Code Exchange)**

✅ **Implemented**: Protects against authorization code interception  
✅ **Method**: S256 (SHA-256) - most secure option  
✅ **Benefit**: Safe for mobile and desktop clients, recommended for all clients

### 2. **State Parameter**

✅ **Implemented**: Prevents Cross-Site Request Forgery (CSRF) attacks  
✅ **Validation**: Compared on callback to ensure request integrity  
✅ **Randomness**: Generated using `secrets.token_urlsafe()` (cryptographically secure)

### 3. **Access Token Security**

✅ **Never exposed to browser**: Only used server-to-server  
✅ **Short-lived**: Typical expiration 1 hour  
✅ **Bearer scheme**: Standard OAuth 2.0 token delivery  

### 4. **ID Token Handling**

✅ **Stored server-side**: In Flask session, not exposed to frontend  
✅ **JWT format**: Can be validated (though Okta signature already verified)  
✅ **Logout use**: Retrieved for single sign-out functionality  

### 5. **Session Security**

⚠️ **Current Implementation**: Flask default session (client-side encrypted cookies)  
✅ **Enhanced Options**:
   - Use Redis for server-side sessions in production
   - Set secure flag for HTTPS-only transmission
   - Implement session timeout/expiration
   - Use SameSite cookie attribute

### 6. **Environment Secrets**

✅ **Never hardcoded**: All secrets loaded from `.env`  
✅ **Git ignored**: `.env` file excluded from version control  
⚠️ **Best Practice**: Use environment variables or secret management services (AWS Secrets Manager, HashiCorp Vault, etc.) in production

### 7. **HTTPS Requirement**

⚠️ **Development**: Uses HTTP for local testing  
✅ **Production**: MUST use HTTPS  
  - Encrypts all traffic between client and server
  - Required by Okta for production domains
  - Protect access tokens and ID tokens in transit

### 8. **CORS Configuration**

✅ **Enabled**: Allows cross-origin requests  
⚠️ **Production**: Configure to allow only trusted domains
   ```python
   CORS(app, resources={r"/api/*": {"origins": "https://trusted-domain.com"}})
   ```

### 9. **Error Handling**

⚠️ **Current**: Returns plain text error messages  
✅ **Production**: Implement proper error handling
   - Log errors securely (no sensitive data)
   - Return generic error messages to users
   - Monitor for authentication failures

### 10. **Secure Redirect Validation**

✅ **Best Practice**: Validate all redirect URIs
   - Only allow registered redirect URIs
   - Prevent open redirect vulnerabilities
   - Validate post-logout redirect URIs

---

## Troubleshooting

### Issue: "The app state doesn't match"

**Cause**: State parameter validation failed  
**Solutions**:
- Ensure cookies are enabled in browser
- Check for multiple browser tabs or concurrent requests
- Verify `session['app_state']` is preserved between requests

### Issue: "Unsupported token type"

**Cause**: Okta returned error during token exchange  
**Solutions**:
- Verify Client ID and Client Secret are correct
- Check Client Secret hasn't expired
- Ensure authorization code hasn't already been exchanged
- Verify code_verifier is correctly calculated from code_challenge

### Issue: Redirect URI mismatch error

**Cause**: Redirect URI in request doesn't match Okta configuration  
**Solutions**:
```python
# Ensure this matches exactly:
OKTA_REDIRECT_URI=http://localhost:5000/callback

# Must be registered in Okta application settings
```

### Issue: "Invalid client_secret"

**Cause**: Incorrect or expired client secret  
**Solutions**:
- Regenerate Client Secret in Okta Admin Console
- Copy entire secret (no extra spaces)
- Verify in `.env` file

### Issue: UserInfo request fails (401 Unauthorized)

**Cause**: Invalid or expired access token  
**Solutions**:
- Verify token exchange succeeded (check response)
- Ensure Bearer token format: `Authorization: Bearer TOKEN`
- Check token hasn't expired

### Issue: Profile page shows "Not Authenticated"

**Cause**: Flask session not properly established  
**Solutions**:
- Check `login_user(user)` was called in callback
- Verify `@login_required` decorator is active
- Check session cookie exists and is valid
- Clear browser cookies and retry login

### Issue: CORS errors in browser console

**Cause**: Cross-origin requests blocked  
**Solutions**:
- Flask-CORS already enabled (`CORS(app)`)
- Ensure requests use correct base URL
- Check browser console for specific origin errors

### Issue: "Authorization code already used"

**Cause**: Authorization code exchanged multiple times  
**Solutions**:
- Authorization codes are single-use
- Redirect loop causing multiple callback attempts
- Clear session and restart sign-in process

### Debug Mode

Enable detailed logging:

```python
# In app.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add to endpoints:
logger.debug(f"State validation: {session.get('app_state')} == {app_state}")
logger.debug(f"Exchange response: {exchange}")
```

---

## References

### Okta Documentation

- [Okta OAuth 2.0 Overview](https://developer.okta.com/docs/concepts/oauth-openid/)
- [Okta Authorization Servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [PKCE Support](https://developer.okta.com/docs/guides/implement-authorization-code-pkce/)
- [OpenID Connect Basics](https://developer.okta.com/docs/concepts/oauth-openid/#openid-connect)
- [Okta API Reference](https://developer.okta.com/docs/api/)

### OAuth 2.0 & PKCE Standards

- [RFC 6749 - OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [RFC 7636 - PKCE (Proof Key for Code Exchange)](https://tools.ietf.org/html/rfc7636)
- [RFC 6234 - US Secure Hash and HMAC Standards](https://tools.ietf.org/html/rfc6234)
- [RFC 8252 - OAuth 2.0 for Native Apps](https://tools.ietf.org/html/rfc8252)

### Flask & Security

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP OAuth 2.0 Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth_2_Cheat_Sheet.html)

### Related Topics

- [JWT (JSON Web Tokens)](https://jwt.io/)
- [HTTPS & TLS Security](https://www.ssl.com/)
- [HTTP Cookies Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
- [CSRF (Cross-Site Request Forgery) Prevention](https://owasp.org/www-community/attacks/csrf)

---

## Production Deployment Checklist

- [ ] Switch to HTTPS (required for Okta)
- [ ] Use environment variables for all secrets (no `.env` in production)
- [ ] Implement server-side session storage (Redis, database)
- [ ] Enable secure cookie flags (`Secure`, `HttpOnly`, `SameSite`)
- [ ] Set proper `Content-Security-Policy` headers
- [ ] Implement request rate limiting
- [ ] Add comprehensive error logging and monitoring
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set `debug=False` in Flask configuration
- [ ] Implement HTTPS redirect
- [ ] Validate all redirect URIs
- [ ] Test single sign-out functionality
- [ ] Implement session timeout/refresh
- [ ] Add CSRF protection for state management
- [ ] Monitor and audit authentication events

---

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

## License

This project is open source and available under the MIT License.

---

## Support

For issues related to:
- **Okta Integration**: See [Okta Developer Support](https://developer.okta.com/docs/)
- **Flask Specifics**: Check [Flask Documentation](https://flask.palletsprojects.com/)
- **This Repository**: Open an issue on GitHub

---

## Author

**Isuruvh** - [GitHub Profile](https://github.com/Isuruvh)

---

**Last Updated**: August 2026  
**Python Version**: 3.8+  
**Framework**: Flask 2.0+
