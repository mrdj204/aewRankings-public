"""
Module: titles.py

This module contains endpoints for displaying titles and information about specific titles.

API Endpoints:
    - /titles: Retrieve and display a list of titles.
    - /titles/{title_name}: Retrieve and display information for a specific title.
"""

from fastapi import APIRouter

from website.resources import (db, Depends, HTTPException, html_table, PERMISSION_ERROR, Request,
                               return_error, SessionData, TemplateResponse)
from website.session import get_session_info

router = APIRouter()


@router.get("/titles/")
async def get_titles(request: Request, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display a list of titles.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    titles, reigns, owners = db.api_titles()
    titles = html_table(titles, id="titles_table")
    reigns = html_table(reigns, id="reigns_table")
    owners = html_table(owners, id="owners_table")

    results = {
        "request": request,
        "current_page": "titles",
        "session": session_data,
        "titles": titles,
        "reigns": reigns,
        "owners": owners,
    }
    return TemplateResponse("titles/titles.html", results)


@router.get("/titles/{title_name}/")
async def get_title(request: Request, title_name, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to retrieve and display information for a specific title.

    Args:
        request (Request): The request object.
        title_name (str): The specific title to retrieve information for.
        session_info (dict): Information about the current session.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    title = db.get_title(title_name)
    if title is None:
        raise HTTPException(status_code=404, detail=f"{title_name} not found")

    owners, matches = title.api_title()
    owners = html_table(owners, id="owners_table")
    matches = html_table(matches, id="matches_table")

    results = {
        "request": request,
        "current_page": "titles",
        "session": session_data,
        "name": title.name,
        "championship": title.championship,
        "owners": owners,
        "matches": matches,
    }
    return TemplateResponse("titles/title.html", results)
