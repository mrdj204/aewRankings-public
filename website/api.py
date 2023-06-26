"""
api.py

This module provides the API routes and exception handlers for a FastAPI based website.
It initializes the FastAPI application, registers the middlewares, exception handlers,
and includes routers from different modules.

Third-party libraries used:
- fastapi
- starlette

Usage:
    This file is intended to be used by a FastAPI server instance to serve the website.

TODO:
    robots.txt
    change no-footer to make footer not sticky instead
"""

# Standard Library Imports
from datetime import datetime
from typing import Callable
from uuid import uuid4

# Third-party Imports
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse, Response
from starlette.staticfiles import StaticFiles

# Local / Custom Imports
from website import sql_db
from website.resources import *
from website.routes import admin, fanhub, stats, titles, wrestlers
from website.session import get_session_info, COOKIE_NAME, SECRET_KEY

# TODO: reach out to AEW metrics on Twitter
# TODO: Support Page: contact info, bug reports, feature requests, patreon, allelitedatabase info/patreon
# TODO: setup reddit, patreon

app = FastAPI()
app.mount("/static", StaticFiles(directory="website/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """
    Custom handler for HTTP exceptions.

    If the HTTP exception status code is 404, this handler redirects
    the user to the root URL. For all other HTTP exceptions, it defers
    to the default FastAPI exception handler.
    """
    # Redirect to the root URL if the status code is 404 (Not Found)
    if exc.status_code == 404:
        return RedirectResponse(url="/")

    # Delegate to the default FastAPI exception handler for other HTTP exceptions
    return await http_exception_handler(request, exc)


@app.middleware("http")
async def log_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for logging user activities.

    This middleware logs user activities if the server is not running locally
    and if the ENABLE_LOGGING flag is set to True in the resources.
    """
    if SERVER_IP != MY_IP and ENABLE_LOGGING:
        time_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        sql = sql_db.SQLDatabase()
        sql.add_user_activity(SERVER_IP, "guest", time_str, request.url.path)
        sql.close()

    # Call the next middleware or route handler
    return await call_next(request)


# Below are the route handlers
@app.get("/login")
async def read_current_user(request: Request, username: str = Depends(get_current_username2)):
    """
    Route for user login.

    Authenticates the user, creates a new session, and saves it in the backend.
    If running locally, saves the backend state to avoid re-login on every server reload.
    """
    session_data = SessionData(
        username=str(username),
        web_user=True,
        web_admin=username in ADMIN_USERS,
        fanhub_user=username in ADMIN_USERS,
        fanhub_elite=username in ADMIN_USERS,
        fanhub_admin=username in ADMIN_USERS,
    )
    session_id = uuid4()
    await backend.create(session_id, session_data)

    # If running locally, save the backend so I don't have to login every server reload
    if SERVER_IP == MY_IP:
        pickle_save("backend", backend)

    cookie = f"{COOKIE_NAME}={session_id}; HttpOnly; Max-Age=1209600; Path=/; SameSite=Lax"
    headers = {"Set-Cookie": cookie}
    results = {
        "request": request,
        "current_page": "home",
        "session": session_data,
        "date_last_updated": db.date_last_updated,
    }

    return TemplateResponse("base.html", results, headers=headers)


@app.get("/discord/login")
async def discord_login() -> RedirectResponse:
    """
    Login via Discord. Redirects the user to Discord for authentication.
    """
    return discord_client.redirect()


@app.get("/discord/callback")
async def callback(request: Request, code: str) -> RedirectResponse:
    """
    Handle Discord OAuth2 callback.

    Validates the Discord session and creates a cookie for the session if valid.
    """
    discord_session = discord_client.session(code)
    session_data = await discord_session.get_fanhub_roles()

    if not session_data:
        error = {"error": "User does not have permissions"}
        return await return_error(request, error)

    # Create a session cookie
    session_id = uuid4()
    await backend.create(session_id, session_data)

    headers = {
        "Set-Cookie": f"{COOKIE_NAME}={session_id}; HttpOnly; Max-Age=1209600; Path=/; SameSite=Lax"
    }
    return RedirectResponse(url="/", headers=headers)


@app.get("/")
async def root(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Handle root endpoint.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]

    results = {
        "request": request,
        "current_page": "home",
        "session": session_data,
        "date_last_updated": db.date_last_updated,
    }
    return TemplateResponse("base.html", results)


@app.get("/faq/")
async def faq(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Handle FAQ endpoint.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        error = {"error": "user doesnt have permission"}
        return await return_error(request, error)

    results = {
        "request": request,
        "current_page": "home",
        "session": session_data,
    }
    return TemplateResponse("faq.html", results)


# Include routers from different modules
app.include_router(wrestlers.router)
app.include_router(stats.router)
app.include_router(titles.router)
app.include_router(admin.router)
app.include_router(fanhub.router)
