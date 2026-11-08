"""Flask application for Okta authentication."""

import base64
import hashlib
import os
import secrets

import dotenv
import ngrok
import requests
from flask import Flask, render_template, redirect, request, session, url_for
from flask_cors import CORS
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from user import User

dotenv.load_dotenv()
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', secrets.token_urlsafe(32)),
    'SESSION_COOKIE_SECURE': False,  # Set to True if using HTTPS
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
})
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """Retrieve a user by ID for Flask-Login."""
    return User.get(user_id)

@app.route("/")
def home():
    """Render the sign-in page."""
    return render_template("signin.html")

config = {
    "auth_uri": os.getenv('OKTA_AUTH_URI'),
    "client_id": os.getenv('OKTA_CLIENT_ID'),
    "client_secret": os.getenv('OKTA_CLIENT_SECRET'),
    "redirect_uri": os.getenv('OKTA_REDIRECT_URI'),
    "issuer": os.getenv('OKTA_ISSUER'),
    "token_uri": os.getenv('OKTA_TOKEN_URI'),
    "userinfo_uri": os.getenv('OKTA_USERINFO_URI')
}

refresh_tokens = {}

@app.route("/signin")
def signin():
    """Redirect the user to Okta to begin authentication."""
    session.permanent = True  # Make session permanent
    session['app_state'] = secrets.token_urlsafe(64)

    # --- PKCE (commented out for plain Authorization Code flow) ---
    session['code_verifier'] = secrets.token_urlsafe(64)
    
    hashed = hashlib.sha256(session['code_verifier'].encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii').strip('=')

    query_params = {'client_id': config["client_id"],
                    'redirect_uri': config["redirect_uri"],
                    'scope': "openid profile offline_access",  # email scope intentionally omitted
                    'state': session['app_state'],
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256',
                    'response_type': 'code',
                    'response_mode': 'query'}

    request_uri = f"{config['auth_uri']}?{requests.compat.urlencode(query_params)}"

    return redirect(request_uri)

@app.before_request
def check_valid_signin():
    """Show the sign-in page when a protected endpoint is requested anonymously."""
    # Fixed string matching for endpoint checking rather than string path matching
    if request.endpoint in ('profile', 'signout') and not current_user.is_authenticated:
        return render_template('signin.html', next=request.endpoint)
    return None

@app.route("/signout", methods=["GET", "POST"])
@login_required
def signout():
    """Sign out the user and redirect to Okta's logout endpoint."""
    # 1. Get the stored id_token before clearing session data
    id_token = session.get("id_token")
    user_id = current_user.get_id()
    
    # 2. Clear Flask-Login tracking
    logout_user()
    
    # 3. Completely clear the Flask browser session cookies
    refresh_tokens.pop(user_id, None)
    session.clear()
    
    # 4. If an id_token exists, build the Okta logout redirection URL
    if id_token and config["issuer"]:
        # Derive Okta logout endpoint from issuer base string
        logout_base = f"{config['issuer']}/v1/logout" if "oauth2" in config['issuer'] else f"{config['issuer']}/oauth2/v1/logout"
        
        query_params = {
            "id_token_hint": id_token,
            "post_logout_redirect_uri": "http://localhost:5000/"  # Points back to your root app signin page
        }
        
        logout_uri = f"{logout_base}?{requests.compat.urlencode(query_params)}"
        return redirect(logout_uri)

    # Fallback option if token wasn't found
    return redirect(url_for("home"))

@app.route("/callback")
@app.route("/authorization-code/callback")
def callback():
    """Handle the authorization-code callback from Okta."""
    session.permanent = True  # Make session permanent
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    app_state = request.args.get("state")
    expected_state = session.get('app_state')
    if not expected_state or app_state != expected_state:
        # Debug: log the mismatch
        print(f"State mismatch - Expected: {expected_state}, Got: {app_state}")
        print(f"Session contents: {dict(session)}")
        return "The app state doesn't match", 403
    if not code:
        return "The code wasn't returned or isn't accessible", 403
        
    query_params = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': request.base_url,
                    'code_verifier': session['code_verifier'],  # PKCE required
                    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=query_params,
        auth=(config["client_id"], config["client_secret"]),
        timeout=10,
    ).json()

    if not exchange.get("token_type"):
        print(f"Token exchange error: {exchange}")
        return "Unsupported token type. Should be 'Bearer'.", 403
        
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]

    # Save ID token in Flask session for the logout step later
    session["id_token"] = id_token

    userinfo_response = requests.get(config["userinfo_uri"],
                                    headers={'Authorization': f'Bearer {access_token}'},
                                    timeout=10).json()

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response.get("email", "")
    user_name = userinfo_response["given_name"]
    refresh_token = exchange.get("refresh_token")
    if refresh_token:
        refresh_tokens[unique_id] = refresh_token

    user = User(
        id_=unique_id, name=user_name, email=user_email
    )

    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    login_user(user)

    return redirect(url_for("profile"))

@app.route("/profile")
@login_required
def profile():
    """Render the authenticated user's profile page."""
    return render_template(
        "profile.html",
        user=current_user,
        refresh_token_received=current_user.get_id() in refresh_tokens,
    )

if __name__ == '__main__':
    # Keep the execution code block at the very bottom
    app.run(host="localhost", port=5000, debug=True)
def connect_ngrok():
    """Start the ngrok tunnel for the local application."""
    forwarder = ngrok.forward(  # pylint: disable=no-member
        "localhost:8085",
        authtoken_from_env=True,
        domain="esteemed-omit-creme.ngrok-free.dev",
    )
    print(f"Available at: {forwarder.url()}")
connect_ngrok()