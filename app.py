import base64
import hashlib
import os
import secrets

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from user import User

load_dotenv()
app = Flask(__name__)
app.config.update({'SECRET_KEY': secrets.token_hex(64)})
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

config = {
    "auth_uri": os.getenv('AUTH_URL'),
    "client_id": os.getenv('CLIENT_ID'),
    "client_secret": os.getenv('CLIENT_SECRET'),
    "redirect_uri": os.getenv('REDIRECT_URI'),
    "issuer": os.getenv('ISSUER'),
    "token_uri": os.getenv('TOKEN_URI'),
    "userinfo_uri": os.getenv('USERINFO_URI')
}


def build_signin_context():
    """Create session values and template variables for the Okta widget."""
    if 'app_state' not in session:
        session['app_state'] = secrets.token_urlsafe(64)
    if 'code_verifier' not in session:
        session['code_verifier'] = secrets.token_urlsafe(64)

    hashed = hashlib.sha256(session['code_verifier'].encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii').rstrip('=')

    issuer = config["issuer"] or ""
    auth_uri = config["auth_uri"] or ""

    # Prefer ISSUER for widget auth configuration; derive base org URL from issuer.
    if issuer and '/oauth2' in issuer:
        base_okta_url = issuer.split('/oauth2')[0]
    elif auth_uri and '/oauth2' in auth_uri:
        base_okta_url = auth_uri.split('/oauth2')[0]
    else:
        base_okta_url = issuer or auth_uri

    return {
        "client_id": config["client_id"] or "",
        "redirect_uri": config["redirect_uri"] or "",
        "issuer": issuer,
        "base_url": os.getenv('BASE_URL') or base_okta_url,
        "state": session['app_state'],
        "code_challenge": code_challenge,
    }


@app.route("/")
def home():
    return redirect(url_for("signin"))


@app.route("/signin")
def signin():
    return render_template("signin.html", **build_signin_context())


@app.route("/signout", methods=["GET", "POST"])
@login_required
def signout():
    logout_user()
    return redirect(url_for("signin"))


@app.route("/callback")
@app.route("/fallback")
def callback():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    app_state = request.args.get("state")

    if app_state != session.get('app_state'):
        return "The app state doesn't match", 403

    if not code:
        return "The code wasn't returned or isn't accessible", 403

    code_verifier = session.get('code_verifier')
    if not code_verifier:
        return "PKCE code verifier is missing from the session. Start a new sign-in attempt.", 403

    # Simplified — requests handles form encoding automatically
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config["redirect_uri"],
        'code_verifier': code_verifier
    }

    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=data,
        auth=(config["client_id"], config["client_secret"])
    )

    try:
        exchange_payload = exchange.json()
    except ValueError:
        return f"Token endpoint returned a non-JSON response: {exchange.text}", 502

    if not exchange.ok:
        error = exchange_payload.get("error", "unknown_error")
        description = exchange_payload.get("error_description", exchange.text)
        return f"Token exchange failed: {error}. {description}", exchange.status_code

    # Validate token response
    token_type = exchange_payload.get("token_type", "")
    if token_type.lower() != "bearer":
        return f"Unsupported token type returned by Okta: {token_type or 'missing'}", 403

    access_token = exchange_payload.get("access_token")
    id_token = exchange_payload.get("id_token")
    if not access_token or not id_token:
        return "Token exchange succeeded but required tokens were missing from the response.", 502

    session.pop('app_state', None)
    session.pop('code_verifier', None)

    # Get userinfo
    userinfo_response = requests.get(
        config["userinfo_uri"],
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]

    user = User(id_=unique_id, name=user_name, email=user_email)

    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    login_user(user)

    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    return render_template("profile.html", user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)
