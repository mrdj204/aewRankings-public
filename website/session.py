"""
session.py

This module handles session management for the website.

It provides functions and classes to handle session information and verification.

Functions:
    - get_session_info: Get session information from the request.

Classes:
    - BasicVerifier: A session verifier implementation for basic session verification.

Constants:
    - COOKIE_NAME: The name of the session cookie.

Dependencies:
    - os
    - uuid
    - dotenv
    - fastapi
    - fastapi_sessions
    - Local modules: website.util, website.models
"""
import os
import uuid
from typing import Union
from uuid import UUID

from dotenv import load_dotenv
from fastapi import HTTPException, Request, Response
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

from website import util
from website.models import SessionData


# Load environment variables
load_dotenv()
my_ip = os.environ.get("MY_IP")
server_ip = util.get_public_IP()
SECRET_KEY = os.environ.get("SECRET_KEY")

# Constants
COOKIE_NAME = "session_id"

# Configuration for session cookie parameters
cookie_params = CookieParameters()

# Session cookie configuration
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key=SECRET_KEY,
    cookie_params=cookie_params,
)

# Initialize session backend
backend = False
# Load backend if local for development purposes
if server_ip == my_ip:
    backend = util.pickle_load("backend")
if not backend:
    backend = InMemoryBackend[UUID, SessionData]()


async def get_session_info(request: Request, response: Response) -> dict[str, Union[str, SessionData]]:
    """
    Get session information from the request.

    Args:
        request (Request): The request object.
        response (Response): The response object.

    Returns:
        dict[str, Union[str, SessionData]]: A dictionary containing the session information or an error.
    """
    session = request.cookies.get(COOKIE_NAME)

    error_data = SessionData(
        username="guest",
        web_user=False,
        web_admin=False,
        fanhub_user=False,
        fanhub_elite=False,
        fanhub_admin=False,
    )

    if not session:
        return {
            "error": "no cookie found",
            "data": error_data,
        }

    if uuid.UUID(session) not in backend.data:
        response.delete_cookie(COOKIE_NAME)
        return {
            "error": "no session found for cookie",
            "data": error_data,
        }

    return {
        "error": None,
        "data": backend.data[uuid.UUID(session)],
    }


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    """
    A session verifier implementation for basic session verification.

    Attributes:
        identifier (str): The identifier for the verifier.
        auto_error (bool): Flag indicating whether to raise an error automatically.
        memory_backend (InMemoryBackend[UUID, SessionData]): The in-memory session backend.
        auth_http_exception (HTTPException): The HTTPException to raise for authentication errors.
    """
    def __init__(
            self,
            *,
            identifier: str,
            auto_error: bool,
            memory_backend: InMemoryBackend[UUID, SessionData],
            auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._memory_backend = memory_backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._memory_backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True
