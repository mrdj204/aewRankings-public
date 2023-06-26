"""
resources.py

This module contains resources and utilities needed for the web application,
such as database initialization, user verification, and configuration settings.

Module Components:
- load_db: Function to load the database.
- return_error: Function to generate an error page.
- get_current_username: Retrieve the current username if the credentials match or return False.
- get_current_username2: Retrieve the current username if the credentials match or raise HTTPException.

Global Variables:
- MY_IP: IP address retrieved from environment variables.
- SERVER_IP: Public IP address of the server.
- SECRET_KEY: Secret key retrieved from environment variables.
- DISABLE_RANKINGS: Flag to disable rankings.
- ENABLE_LOGGING: Flag to enable logging.
- templates: Jinja2Templates object for rendering templates.
- TemplateResponse: Alias for TemplateResponse from starlette.templating.
- db: Global variable for storing the database instance.
- RANKINGS_USER: Name of the rankings user. This is fanhub and to be moved.
- security: HTTPBasic object for basic authentication.
- security2: HTTPBasic object for basic authentication with auto error handling.
- discord_client: CustomDiscordOAuthClient object for Discord OAuth configuration.
- verifier: BasicVerifier object for user verification.

Dependencies:
- secrets
- os
- fastapi
- starlette
- dotenv
- logging
- Local modules: mmr_database, website.discord, website.models, website.resources_private,
  website.session, website.util
"""

# Standard Library Imports
import secrets
from typing import Optional

# Third-party Imports
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status
from starlette.requests import Request
from starlette.templating import Jinja2Templates

# Local / Custom Imports
from mmr_database.mmrDB import mmrDB
from website.discord import CustomDiscordOAuthClient
from website.models import SessionData
from website.resources_private import *
from website.session import BasicVerifier, backend
from website.util import *

# Load environment variables
load_dotenv()
MY_IP = os.environ.get("MY_IP")
SERVER_IP = get_public_IP()

# Configuration flags
DISABLE_RANKINGS = False
ENABLE_LOGGING = False

# Constants
PERMISSION_ERROR = {"error": "User doesn't have permission"}

# Initialize templates
templates = Jinja2Templates(directory="website/templates")
TemplateResponse = templates.TemplateResponse


def load_db():
    """
    Load the database into the global variable `db`.

    The function makes use of the `mmrDB` class and the `DISABLE_RANKINGS` flag.
    It's crucial to set the appropriate value for `DISABLE_RANKINGS` before invoking this function.
    """
    global db
    db = mmrDB(DOWNLOAD_DB=False, DISABLE_RANKINGS=DISABLE_RANKINGS)


# Load database
db: Union[mmrDB, None] = None
load_db()

# TODO: need to move
# Placeholder variable for fanhub resources
RANKINGS_USER = "current_rankings"

# Security configuration
security = HTTPBasic(auto_error=False)
security2 = HTTPBasic(auto_error=True)

# Discord OAuth client configuration
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
callback = os.environ.get("CALLBACK")
scopes = ("guilds.members.read", "guilds", "email", "identify")
discord_client = CustomDiscordOAuthClient(client_id, client_secret, callback, scopes)

# Initialize verifier
verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    memory_backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


async def return_error(request: Request, error: dict):
    """
    Return an error page with the provided error information.

    Parameters:
    - error (dict): A dictionary containing error information.

    Returns:
    - TemplateResponse: A rendered error page.
    """
    data = SessionData(
        username="guest",
        web_user=False,
        web_admin=False,
        fanhub_user=False,
        fanhub_elite=False,
        fanhub_admin=False,
    )
    results = {
        "request": request,
        "current_page": "home",
        "session": data,
        "error": error,
    }
    return TemplateResponse("error.html", results)


# TODO: Merge these into one function
async def get_current_username(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """
    Retrieve the current username if the credentials match or return False.

    Parameters:
    - credentials (Optional[HTTPBasicCredentials]): The user credentials.

    Returns:
    - str or bool: The current username if the credentials match, False otherwise.

    Note:
    - Most pages use this function to get username and redirect to home if fail.
    """
    if credentials:
        current_username_bytes = credentials.username.encode("utf8")
        current_password_bytes = credentials.password.encode("utf8")

        for saved_user, saved_pass in USER_DB.items():
            if secrets.compare_digest(current_username_bytes, saved_user):
                if secrets.compare_digest(current_password_bytes, saved_pass):
                    return credentials.username

    return False


# TODO: Merge these into one function
async def get_current_username2(credentials: Optional[HTTPBasicCredentials] = Depends(security2)):
    """
    Retrieve the current username if the credentials match or raise an HTTPException.

    Parameters:
    - credentials (Optional[HTTPBasicCredentials]): The user credentials.

    Returns:
    - str: The current username if the credentials match.

    Raises:
    - HTTPException: If the credentials do not match.

    Note:
    - This function is used on the login page to force the login window to reopen if the credentials fail.
    """
    if credentials:
        current_username_bytes = credentials.username.encode("utf8")
        current_password_bytes = credentials.password.encode("utf8")

        for saved_user, saved_pass in USER_DB.items():
            if secrets.compare_digest(current_username_bytes, saved_user):
                if secrets.compare_digest(current_password_bytes, saved_pass):
                    return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )
