import base64
import hashlib
import requests
import secrets
import dotenv
import os
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
app.config.update({'SECRET_KEY': 'qwertyuioplkjhgfdsazxcvbnmlkjhgf'})
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
  return User.get(user_id)
@app.route("/")
def home():
    return render_template("signin.html")

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)

config = {
    "auth_uri": os.getenv('OKTA_AUTH_URI'),
    "client_id": os.getenv('OKTA_CLIENT_ID'),
    "client_secret": os.getenv('OKTA_CLIENT_SECRET'),
    "redirect_uri": os.getenv('OKTA_REDIRECT_URI'),
    "issuer": os.getenv('OKTA_ISSUER'),
    "token_uri": os.getenv('OKTA_TOKEN_URI'),
    "userinfo_uri": os.getenv('OKTA_USERINFO_URI')
}
@app.route("/signin")
def signin():
    # store app state and code verifier in session
    session['app_state'] = secrets.token_urlsafe(64)
    session['code_verifier'] = secrets.token_urlsafe(64)

    # calculate code challenge
    hashed = hashlib.sha256(session['code_verifier'].encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii').strip('=')

    # get request params
    query_params = {'client_id': config["client_id"],
                    'redirect_uri': config["redirect_uri"],
                    'scope': "openid email profile",
                    'state': session['app_state'],
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256',
                    'response_type': 'code',
                    'response_mode': 'query'}

    # build request_uri
    request_uri = "{base_url}?{query_params}".format(
        base_url=config["auth_uri"],
        query_params=requests.compat.urlencode(query_params)
    )

    return redirect(request_uri)
@app.route("/signout", methods=["GET", "POST"])
@login_required
def signout():
    logout_user()
    return redirect(url_for("signin"))
@app.route("/authorization-code/callback")
def callback():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    app_state = request.args.get("state")
    #if app_state != session['app_state']:
    #    return "The app state doesn't match"
    if not code:
            return "The code wasn't returned or isn't accessible", 403
    query_params = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': request.base_url,
                    'code_verifier': session['code_verifier'],
                    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=query_params,
        auth=(config["client_id"], config["client_secret"]),
    ).json()

    # Get tokens and validate
    if not exchange.get("token_type"):
            return "Unsupported token type. Should be 'Bearer'.", 403
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]

    # Authorization flow successful, get userinfo and sign in user
    userinfo_response = requests.get(config["userinfo_uri"],
                                    headers={'Authorization': f'Bearer {access_token}'}).json()

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]

    user = User(
        id_=unique_id, name=user_name, email=user_email
    )

    if not User.get(unique_id):
            User.create(unique_id, user_name, user_email)

    login_user(user)

    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
   return render_template("profile.html", user=current_user)
