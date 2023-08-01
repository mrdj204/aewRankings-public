"""
Module: wrestlers.py

This module contains API endpoints for wrestler info.

API Endpoints:
    - /divisions/{abr}: List of wrestlers in division
    - /wrestlers/{name:path}: Retrieve and display wrestler info.

TODO:
    - redo wrestler page
"""

from datetime import datetime
from urllib.parse import unquote
from mmr_database.division import Division

from website.resources import db, Depends, PERMISSION_ERROR, Request, return_error, SessionData, TemplateResponse
from fastapi import APIRouter

from website.session import get_session_info
from website.util import html_table

router = APIRouter()


@router.get("/divisions/{abr}")
async def get_wrestlers(request: Request, abr: str, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to render a list of wrestlers in a division.

    Args:
        request (Request): The request object.
        abr (str): The specific division to retrieve information for.
        session_info (dict): Information about the current session.
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    division: Division = db.get_division(abr)

    output = {
        "name": division.name,
        "abr": division.abr,
        "wrestlers": html_table(division.api_divisions(), id="division_table"),
    }

    results = {
        "request": request,
        "current_page": "wrestlers",
        "session": session_data,
        "division": output,
        "hide_footer": True,
    }
    return TemplateResponse("wrestlers/division.html", results)


@router.get("/wrestlers/{name:path}")
async def get_wrestler(request: Request, name, session_info: dict = Depends(get_session_info)):
    """
    Endpoint to render wrestler info.

    Args:
        request (Request): The request object.
        name (str): The specific wrestler to retrieve information for.
        session_info (dict): Information about the current session.

    TODO:
        - need to completly rework this page
    """
    if session_info["error"] is not None:
        return await return_error(request, session_info["error"])

    session_data: SessionData = session_info["data"]
    if not session_data.web_user:
        return await return_error(request, PERMISSION_ERROR)

    # why does Trent? need to have a ? in his name...
    query_params = unquote(str(request.query_params)[1:-1])
    if query_params:
        name = name + "? " + str(query_params)

    contestant, division = None, None
    for d in db.divisions:
        contestant = db.get_contestant(d, name)
        if contestant:
            division = d
            break
    else:
        return {"c": contestant, "name": name}

    all_contestants = sorted(division.contestants, key=lambda c: c.mmr_dict[c.main_mmr_keys[0]], reverse=True)

    api_stats = contestant.api_wrestlers()
    stats_html = []
    for year, stat_block in api_stats["stats"].items():
        if "name" in stat_block:
            del stat_block["name"]
        stats = {"year": year}
        stats.update(stat_block)
        # stats_html.append(util.html_table(stats))
        stats_html.append(stats)
    api_stats["stats_html"] = html_table(stats_html)  # stats_html
    api_stats["match_history"] = html_table(api_stats["match_history"], id="match_history")

    record = ""
    if datetime.today().year in api_stats["stats"]:
        record = api_stats["stats"][datetime.today().year]["record"][contestant.main_division_key]
    all_time_record = api_stats["stats"]["alltime"]["record"][contestant.main_division_key]

    results = {
        "request": request,
        "current_page": "wrestlers",
        "session": session_data,
        "all_contestants": all_contestants,
        "datetime": datetime,
        "record": record,
        "all_time_record": all_time_record,
    }
    results.update(api_stats)

    return TemplateResponse("wrestlers/wrestler.html", results)
